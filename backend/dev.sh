#!/bin/bash
# Lance le backend (uvicorn) et le frontend en parallèle, et arrête proprement
# les deux processus si l'un d'eux s'arrête ou si on interrompt le script (Ctrl+C).


source venv/bin/activate

uvicorn main:app --reload --port 3000 &




