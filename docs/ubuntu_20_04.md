# Using Ubuntu 20.04 #

## Setup ##
1. Install Ubuntu (more than one core, 10ish GB RAM, 50+ GB HD)
2. Download OpenStudio 3.7 .deb from GitHub or openstudio.net
3. Install OpenStudio: `sudo dpkg -i OpenStudio-3.7-blah-blah.deb`
4. Verify installation with `openstudio --help`
5. Install pip: `sudo apt install python3-pip`
6. Install git: `sudo apt install git`
7. Make a repo directory, `cd` in and clone the repo (using SSH here): `git clone git@github.com:Stor4Build/stor4build.git .`
8. Install the package: `sudo pip install .`
9. Verify installation with `stor4build --help`
