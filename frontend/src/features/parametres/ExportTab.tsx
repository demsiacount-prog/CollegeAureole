import { useState } from 'react'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage, api } from '@/lib/api'

/** Onglet Paramètres → Export : téléchargement d'une sauvegarde XLSX de
 *  toutes les tables. L'import XLSX a été retiré : l'initialisation des vraies
 *  données passe désormais par le script de seed Python côté serveur. */
export default function ExportTab() {
  const [downloading, setDownloading] = useState(false)

  const handleExport = async () => {
    setDownloading(true)
    try {
      const response = await api.get('/api/import-export/export', { responseType: 'blob' })
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const disposition = response.headers['content-disposition']
      const match = disposition?.match(/filename="?([^"]+)"?/)
      a.download = match?.[1] ?? 'collegeaureole_export.xlsx'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      toast('Export téléchargé avec succès.')
    } catch (e) {
      toast(extractErrorMessage(e, "Erreur lors de l'export."), 'error')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h3 className="mb-4 border-b border-[var(--color-border-soft)] pb-2 text-sm font-semibold text-[var(--color-ink)]">
        Export des données
      </h3>

      <Card className="p-5 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Download size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--color-action)]" />
            <div>
              <p className="text-sm font-medium text-[var(--color-ink)]">Exporter la base de données</p>
              <p className="mt-0.5 text-xs text-[var(--color-ink-dim)]">
                Télécharge un fichier Excel (.xlsx) contenant toutes les données de l&apos;établissement.
                Chaque table est dans un onglet séparé.
              </p>
            </div>
          </div>
          <Button variant="primary" isLoading={downloading} onClick={handleExport} className="shrink-0">
            Télécharger l&apos;export
          </Button>
        </div>
      </Card>
    </div>
  )
}
