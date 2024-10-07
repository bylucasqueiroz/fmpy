import os


def get_file_name(current_year, current_month_name):
    return f'{current_year}_{current_month_name}'

def clen_file(file_path):
    if os.path.exists(file_path):
            os.remove(file_path)
            print(f"{file_path} has been deleted successfully.")
    else:
        print(f"{file_path} does not exist.")