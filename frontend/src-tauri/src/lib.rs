use std::sync::atomic::{AtomicU16, Ordering};
use std::sync::{Arc, Mutex};
use tauri::{Emitter, Manager};
use tauri_plugin_shell::ShellExt;

struct BackendState {
    port: Arc<AtomicU16>,
    child_pid: Mutex<Option<u32>>,
}

#[tauri::command]
fn get_backend_url(state: tauri::State<BackendState>) -> String {
    let port = state.port.load(Ordering::Relaxed);
    format!("http://127.0.0.1:{}", port)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let shell = app.shell();
            let sidecar_command = shell
                .sidecar("college-aureole-backend")
                .expect("failed to create sidecar command");

            let (mut rx, child) = sidecar_command
                .spawn()
                .expect("failed to spawn sidecar");

            let child_pid = child.pid();
            let port = Arc::new(AtomicU16::new(0));
            let port_clone = port.clone();
            let app_handle = app.handle().clone();

            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            let line_str = String::from_utf8_lossy(&line);
                            log::info!("[backend] {}", line_str.trim());
                            if let Some(port_str) =
                                line_str.trim().strip_prefix("AUREOLE_PORT=")
                            {
                                if let Ok(p) = port_str.trim().parse::<u16>() {
                                    log::info!("Backend ready on port {}", p);
                                    port_clone.store(p, Ordering::Relaxed);
                                    if let Err(e) =
                                        app_handle.emit("backend-ready", p)
                                    {
                                        log::error!(
                                            "Failed to emit backend-ready: {}",
                                            e
                                        );
                                    }
                                }
                            }
                        }
                        CommandEvent::Stderr(line) => {
                            log::error!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Terminated(status) => {
                            log::info!("Backend terminated with {:?}", status);
                            break;
                        }
                        _ => {}
                    }
                }
            });

            app.manage(BackendState {
                port,
                child_pid: Mutex::new(Some(child_pid)),
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let state = window.state::<BackendState>();
                let pid = *state.child_pid.lock().unwrap();
                drop(state);
                if let Some(pid) = pid {
                    #[cfg(target_family = "unix")]
                    {
                        let _ = std::process::Command::new("kill")
                            .arg("--")
                            .arg(pid.to_string())
                            .spawn();
                    }
                    #[cfg(target_family = "windows")]
                    {
                        let _ = std::process::Command::new("taskkill")
                            .arg("/F")
                            .arg("/PID")
                            .arg(pid.to_string())
                            .spawn();
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![get_backend_url])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
