import shutil
from werkzeug.utils import secure_filename
import os


def save_files(files):
    print(files)
    for file in files:
        filename = secure_filename(file.filename)
        # 2. Save the file temporarily
        file_path = os.path.join("media", filename)
        file.save(file_path)


def nuke_files():
    if os.path.exists("./media"):
        shutil.rmtree("./media")

    os.mkdir("./media")
