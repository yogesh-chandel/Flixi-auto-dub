# =========================================
# STEP 1: Install Argos Translate
# =========================================

!pip -q install argostranslate


# =========================================
# STEP 2: Import Libraries
# =========================================

from argostranslate import package
from argostranslate import translate


# =========================================
# STEP 3: Download Available Translation Packages
# =========================================

package.update_package_index()

available_packages = package.get_available_packages()


# =========================================
# STEP 4: Select Translation Package
# =========================================
# Example:
# English -> Hindi

from_code = "en"
to_code = "hi"

package_to_install = next(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code,
        available_packages
    )
)


# =========================================
# STEP 5: Install Translation Package
# =========================================

package.install_from_path(package_to_install.download())


# =========================================
# STEP 2: Upload Text File
# =========================================

from google.colab import files

uploaded = files.upload()


# =========================================
# STEP 2: Read Text File
# =========================================

import os

text_file = list(uploaded.keys())[0]

print("Uploaded file:", text_file)

with open(text_file, 'r') as file:
    text = file.read()
print(text)


# =========================================
# STEP 6: Translate Text
# =========================================

translated = translate.translate(
    text,
    from_code,
    to_code
)

print("\nTranslated Text:\n")
print(translated)


# =========================================
# STEP 6: Translate Text
# =========================================

with open("translate.txt", "w", encoding="utf-8") as f:
    f.write(translated)


# =========================================
# STEP 6: Translate Text
# =========================================

files.download("translate.txt")
