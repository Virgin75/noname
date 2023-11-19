#!/bin/bash

BASE_PATH="$(dirname "$0")"
source "bin/colors.sh"
EXIT_CODE=0


################################################################################
#                                   ISORT                                      #
################################################################################
echo -n "${Cyan}Formatting import with isort... $Color_Off"
out=$(isort . --profile black)
if [ ! -z "$out" ] ; then
  echo ""
  echo -e "$out"
fi
echo "${Green}Ok ✅ $Color_Off"
echo ""

################################################################################
#                                   BLACK                                      #
################################################################################
echo "${Cyan}Formatting code with black...$Color_Off"
black --exclude="^.*\b((migrations)|(venv))\b.*$" -l 120 .
echo ""


################################################################################
#                                  FLAKE 8                                     #
################################################################################
echo -n "${Cyan}Running flake8... $Color_Off"
out=$(flake8 .)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################
#                                PYDOCSTYLE                                    #
################################################################################
echo -n "${Cyan}Running pydocstyle... $Color_Off"
out=$(pydocstyle --count)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""

################################################################################
#                                  DJHTML                                     #
################################################################################
echo -n "${Cyan}Running djhtml to reformat HTML templates... $Color_Off"
out=$(djhtml .)
if [ "$?" -ne 0 ] ; then
  echo "${Red}Error !$Color_Off"
  echo -e "$out"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""

################################################################################
#                                MIGRATIONS                                    #
################################################################################
echo -n "${Cyan}Checking for missing migrations... $Color_Off"
out=$(python3 manage.py makemigrations --check --dry-run --no-input &> /dev/null)
if [ "$?" -ne 0 ] ; then
  echo "${Red}migrations are missing !$Color_Off"
  echo "${Red}Run 'python3 manage.py makemigrations' before committing !$Color_Off"
  EXIT_CODE=1
else
  echo "${Green}Ok ✅ $Color_Off"
fi
echo ""


################################################################################


if [ $EXIT_CODE = 1 ] ; then
   echo "${Red}⚠ You must fix the errors before committing ⚠$Color_Off"
fi
echo "${Purple}✨ You can commit without any worry ✨$Color_Off"
