import gettext
import os

# Define the directory where the translation files are located
locales_dir = os.path.join(os.path.dirname(__file__), "locale")

# Set the desired language (e.g., 'en' or 'fr')
language = "eu"

# Initialize gettext and set the _ function globally
_ = gettext.translation("Beremiz", locales_dir, languages=[language]).gettext
