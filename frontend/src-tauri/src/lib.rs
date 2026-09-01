// Client léger College Aureole : la fenêtre embarque l'interface React et
// dialogue avec le backend FastAPI installé sur le même poste (mono-poste).
// Aucun traitement métier ici — tout vit côté serveur.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("erreur lors du lancement de College Aureole");
}
