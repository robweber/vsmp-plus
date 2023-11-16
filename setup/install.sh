#!/bin/bash -e

GIT_REPO=https://github.com/robweber/vsmp-plus
GIT_BRANCH=master
LOCAL_DIR=""
PYTHON_VERSION=3
SKIP_DEPS="false"

# color code variables
RED="\e[0;91m"
YELLOW="\e[0;93m"
RESET="\e[0m"

# file paths
SERVICE_DIR=/etc/systemd/system
SERVICE_FILE=vsmp.service

function install_linux_packages(){
  sudo apt-get update

  sudo apt-get install -y ffmpeg fonts-freefont-ttf git python3-dev python3-rpi.gpio python3-pil python3-numpy python3-pip libopenjp2-7 libtiff6 redis-server usbmount

}

function install_python_packages(){
  # create the virtual environment
  cd $LOCAL_DIR
  python3 -m venv --system-site-packages .venv
  source .venv/bin/activate

  # install requirements
  pip3 install setuptools -U
  pip3 install -r $LOCAL_DIR/setup/requirements.txt

  # deactivate the virtual environment
  deactivate
}

function build_python_libraries(){
  # leave this here as a placeholder, currently all libs in requirements.txt
  cd $HOME
}

function setup_hardware(){
  echo "Setting up SPI"
  if ls /dev/spi* &> /dev/null; then
      echo -e "SPI already enabled"
  else
      if command -v raspi-config > /dev/null && sudo raspi-config nonint get_spi | grep -q "1"; then
          sudo raspi-config nonint do_spi 0
          echo -e "SPI is now enabled"
      else
          echo -e "${RED}There was an error enabling SPI, enable manually with sudo raspi-config${RESET}"
      fi
  fi
}

function install_service(){
  if [ -d "${LOCAL_DIR}" ]; then
    cd $LOCAL_DIR

    # install the service files and enable
    sudo cp setup/$SERVICE_FILE $SERVICE_DIR
    sudo chown root:root "${SERVICE_DIR}/${SERVICE_FILE}"
    sudo systemctl daemon-reload
    sudo systemctl enable slowmovie

    echo -e "VSMP+ service installed! Use ${YELLOW}sudo systemctl start vsmp${RESET} to start"

  else
    echo -e "${RED}VSMP+ repo does not exist!${RESET}"
  fi

  # go back to home
  cd $HOME
}

# get any options
while getopts ":r:b:h" arg; do
    case "${arg}" in
        r)
          GIT_REPO=${OPTARG}
        ;;
        b)
          GIT_BRANCH=${OPTARG}
        ;;
        s)
          SKIP_DEPS="true"
        ;;
        h)
          echo "VSMP Plus Install/Upgrade Script"
          echo "Use this to install or upgrade your VSMP Plus system"
          echo "Usage:"
          echo "[-r] specify a repo url"
          echo "[-b] specify a repo branch"
          echo "[-s] to skip dependency installs (update Git repo only)"
          exit 0
        ;;
    esac
done

# set the local directory
LOCAL_DIR="$HOME/$(basename $GIT_REPO)"

# clear screen
  clear;

  # Set color of logo
  # Logo generated from: http://patorjk.com/software/taag/
  tput setaf 4
  tput bold

  cat << EOF

   _    _______ __  _______
  | |  / / ___//  |/  / __ \     __
  | | / /\__ \/ /|_/ / /_/ /  __/ /_
  | |/ /___/ / /  / / ____/  /_  __/
  |___//____/_/  /_/_/        /_/


EOF

# reset terminal color
tput sgr 0

echo -e "SlowMovie Repo set to ${YELLOW}${GIT_REPO}/${GIT_BRANCH}${RESET}"
echo -e "Setting up in local directory ${YELLOW}${LOCAL_DIR}${RESET}"
echo -e ""

cd $HOME

if [ "${SKIP_DEPS}" = "false" ]; then
  # install from apt
  install_linux_packages

  # configure the hardware
  setup_hardware
else
  echo -e "Skipping dependency installs, updating VSMP+ code only"
fi

if [ -d "${LOCAL_DIR}" ]; then
  echo -e "Existing Install - Running Update"
else
  echo -e "No Install Found - Running Install"
  git clone ${GIT_REPO}
fi

# update the repo
cd ${LOCAL_DIR}
git fetch
git checkout ${GIT_BRANCH}
git pull

if [ "$SKIP_DEPS" = false ]; then
  # install any needed python packages
  install_python_packages

  # install any additional libraries we need to build manually
  build_python_libraries
fi

# install the Service
install_service

# install the usb automount file
sudo cp setup/systemd-udevd.service /lib/systemd/system/systemd-udevd.service

cd $LOCAL_DIR
cp setup/vsmp.conf ./custom-conf.conf

echo -e "VSMP+ install complete"
