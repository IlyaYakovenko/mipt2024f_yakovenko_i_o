#!/bin/bash

# shellcheck disable=SC1090
source ~/.poetry/env
x-terminal-emulator --noclose -e "poetry run python app/main.py"

if [ -z "$1" ]; then
  echo "Ошибка: необходимо указать имя для копии папки."
  exit 1
fi

# Задание пути для новой папки
NEW_FOLDER_NAME="$1"
DESTINATION_PATH="all_outputs/$NEW_FOLDER_NAME"

# Копирование папки output в all_outputs с новым именем
mkdir -p all_outputs
cp -r output "$DESTINATION_PATH"

echo "Папка 'output' успешно скопирована в 'all_outputs' под именем '$NEW_FOLDER_NAME'."
