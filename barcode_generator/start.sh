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
# Проверяем, существует ли папка с заданным именем в "all_outputs"
if [ ! -d "$DESTINATION_PATH" ]; then
  # Если папка не существует, копируем папку "output" и даём ей нужное имя
  cp -r ./output "$DESTINATION_PATH"
  echo "Папка 'output' скопирована в 'all_outputs/$NEW_FOLDER_NAME'."
else
  # Если папка существует, копируем содержимое "output" в существующую папку
  cp -r ./output/* "$DESTINATION_PATH"
  echo "Содержимое папки 'output' добавлено в 'all_outputs/$NEW_FOLDER_NAME'."
fi