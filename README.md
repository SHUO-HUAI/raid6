# raid6

## Process 1 (Main Process)
This process is used for maintaining the RAID6 system, it runs all the time. When it begins, it will wait for all storage processes (N, including _S_ for storage and _P_ for parities) start and build communications with them. In the initial, it will randomly set parities blocks in the same block index among all storage processes.

Then it will wait for user processes to connect it and user processes will send commands (upload, download, modify, delete) to this main process.
>upload _filename_ \
>download _filename_ \
>modity _filename_ _new\_filename_ \
>delete _filename_

It has a file name list to reverse which file is saved in this system. And each file name can refer to a list to indicate which storage process and which block saves this file （这里有问题，因为文件系统的话，所有东西都必须存储在文件系统里面，所以是不存在这些链表的。应该用一块保留区去存取这些东西，那个冗余纠错用的哪个block一起保存， ：Nov08已完成）. It will send the write, read, delete commands to the storage processes （简单起见，更改命令先用删除旧的和创建新的代替）. For upload, the main processes will divide a file to some parts and each part is some times of block size and then it sends each part to a storage process (rank by blank space). Then it will calculate the parities and write parities. For delete, it also needs to modify the parities. For download, it needs to combine all data from each storage process.

## Process 2 (Storage Process) Done: Nov08
This process is used to save data in binary formate. It has _B_ blocks and each block has _K_ Bytes (8*bits). Each block's first _n_ is used to save how many occupied bits in this block. It has a block to save which block has been used. For the write command, it will find a block to write the content in and return the block index (unsuccessful, return -1). For the read command, it will return the content in binary by the block index. For the delete command,  it will set this block to unused and return the index for the main process to modify parities.

## Process 3 (User Process)
This process is used by some users, we can use it to upload, download, delete files.

## For Communication Done: Nov08
As it needs to support multiple machines, we may use network communication (socket?) among all processes.

## For Storage Processes shutdown
The main process will trigger the erasure codes to repair the data （根据课上的内容进行）.

![avatar](https://raw.githubusercontent.com/Shaowen310/raid6/main/imgs/read.png?token=ANCBBUKLP4HVGJWPJR6ZNPC7U6Z6Y)
