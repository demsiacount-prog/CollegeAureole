import { useAnneeActive } from './useAnneeActive'

/** Lecture seule : l'année scolaire sélectionnée (active) est clôturée.
 *  Dans ce mode, toute l'application est consultable mais aucune écriture
 *  n'est exposée (canWrite = !lectureSeule). */
export function useLectureSeule() {
  const { data: annee } = useAnneeActive()
  return { lectureSeule: annee?.cloturee === true }
}