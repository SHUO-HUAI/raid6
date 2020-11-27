# raid6
This repository is used for the RAID 6 project for CE7490 Advanced Topics in Distributed Systems.

## Instructions
This code is developed under Ubuntu 16.04 x64 OS and Python 3.5 Development Environment. The package we only require is NumPy-1.17.2. Next, you can clone this
repository.
> git clone git@github.com:Shaowen310/raid6.git \
> cd raid6

Then there are three *_process.py files for a different function. Storage process and User process will interaction will the Main process. So you can run these three
files on different machines, only need to know the IP of Main process.

Run Main process by:
> python main_process.py --some_configs
>
Then you need to start N storage process, N is defined in config.py, each storage process is executed by the following command:
> python storage_process.py --some_configs

Finally, you can use User process for saving and reading data from the RAID 6 system by:
> python user_process.py --some_configs

And the commands for user process are following:
>upload _filename_ \
>download _filename_ \
>modity _filename_ \
>delete _filename_

## Features
- File system operations:
    - Read
    - Write
    - Delete
    - Modify
- RAID 6 operations:
    - Two parities blocks
    - Recover broken <= 2 disks
    - Find which storage is failed by network connection and parities
    - Support n+2 configurations, n(>=2) for storage, 2 for parities
-  Data structure:
    - Any size of data and any type of data
    - A list is used to map the filename to its location, mutable files
    - Fixed-size of binary files to simulate physical storage blocks for storage
- Network Storage:
    - Support each storage process on a different machine
    - Socket technique is used