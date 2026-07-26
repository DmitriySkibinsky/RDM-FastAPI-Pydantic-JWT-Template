import os
import subprocess


def run_command(cmd, description):
    """Запускает команду и выводит результат"""
    print(f"\n📋 {description}...")
    print(f"   Команда: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"   ❌ Ошибка: {result.stderr}")
            return False
        else:
            if result.stdout.strip():
                print(f"   ✅ Вывод: {result.stdout}")
            return True
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False


def main():
    """Основная функция"""
    print("🧹 Начинаем форматирование кода...")

    # 1. Очистка кэша
    print("\n1. Очистка кэша Python...")
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_dir = os.path.join(root, dir_name)
                try:
                    import shutil

                    shutil.rmtree(cache_dir)
                    print(f"   Удалено: {cache_dir}")
                except:
                    pass

    # 2. Сортировка импортов
    if not run_command("isort .", "Сортировка импортов с isort"):
        print("\n⚠️  isort не установлен. Установите: pip install isort")

    # 3. Форматирование black
    if not run_command("black .", "Форматирование кода с black"):
        print("\n⚠️  black не установлен. Установите: pip install black")

    # 4. Проверка flake8
    if not run_command(
        "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics",
        "Проверка критических ошибок",
    ):
        print("\n⚠️  Критические ошибки найдены!")

    # 5. Проверка стиля
    run_command(
        "flake8 . --count --exit-zero --max-complexity=10 --max-line-length=79 --statistics",
        "Проверка стиля кода",
    )

    print("\n✅ Форматирование завершено!")


if __name__ == "__main__":
    main()
