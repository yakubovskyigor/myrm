# MYRM

It is the command-line tool that allows you to manage the main file system on a local or remote machine.
With this tool, you can delete an item or a group of items to the bucket, recording the original path and time of deletion or delete items permanently.
You can delete items using regular expressions.
Also, view the contents of the bucket and set configuration parameters for it, such as the maximum size and time to clean up the bucket.

Basic commands for using the tool:

```bash
myrm rm             move item or items to the bucket or delete permanently;
myrm show           show contents of the bucket;
myrm restore        restore an item or a group of items from the bucket;
myrm bucket         manage a specified bucket;
```

## Installation
Use the package manager pip to install myrm with the command-line interface:

```bash
python3 -m pip install 'git+https://github.com/yakubovskyigor/rmlib.git'
```

You can also install this python package on your working machine from source code:
```bash
# Step -- 1.
git clone --depth=1 --branch=main 'https://github.com/yakubovskyigor/rmlib.git'

# Step -- 2.
cd ./rmlib/

# Step -- 3.
python3 setup.py install
```

## Using as the command-line tool
Before the first usage, you are to generate a new settings file:
```bash
myrm --generate-settings
```
This command creates a new settings file at the default path `~/.config/myrm/settings.json` on the working machine.

---
### `myrm rm`
This command is used to move files or folders to the bucket:

```bash
# Step -- 1.
mkdir test &&
touch test.txt &&
touch test/test.txt

# Step -- 2.
myrm rm test.txt

# Step -- 3.
myrm rm test

# Step -- 4.
ls -la test test.txt
```

### `myrm rm` with `--regex` or `-r` flag
This command allows you to move specified items to the bucket using regular expressions:

```bash
# Step -- 1.
mkdir test
cd test

# Step -- 2.
touch test.txt test.png test.bin

# Step -- 3.
ls
test.bin  test.png  test.txt

# Step -- 4.
myrm rm ./ --regex '*.png'

# Step --5.
ls
test.bin test.txt
```

> Note: you need to use single quotes to protect the template from shell expansion.

> Caution: you are to input a path for `myrm rm` command before you input `--regex` with the regular expression.

### `myrm rm` with `--force` or `-f` flag
This command allows you to permanently delete the specified items from the current machine:

```bash
# Step -- 1.
touch test.txt

# Step -- 2.
myrm rm test.txt --force
Do you want to delete item(s)? (yes/no):
yes # or "y"

# Step -- 3.
myrm show
2022-07-17--10-00-00 - WARNING :: myrm :: History is empty.
```

### `myrm rm` with `--confirm` or `-c` flag
This command allows you to perform destructive actions (`rm --force` and `bucket --cleanup`) without confirmation:

```bash
# Step -- 1.
touch test.txt

# Step -- 2.
myrm rm test.txt --force --confirm

# Step -- 3.
myrm show
2022-07-17--10-00-00 - WARNING :: myrm :: History is empty.
```

---
### `myrm show`
This command shows the table with deleted items on the current machine:

```bash
# Step -- 1.
touch test.txt
mkdir test

# Step -- 2.
myrm rm test.txt test

# Step -- 3.
myrm show
Status    Index    Name      Origin                    Removed on
--------  -------  --------  ------------------------  ----------------------
OK              1  test.txt  /home/user_name/test.txt  2022-07-17 10:00:00 AM
OK              2  test      /home/user_name/test      2022-07-17 10:00:00 AM
```
Description of table column names:

- Status - checks whether the object was moved to the trash correctly;
- Index - the ordered number of the object in the bucket;
- Name - the original name of the object moved to the bucket;
- Origin - the path to the object before it is moved to the bucket;
- Removed on - time when object was moved to the bucket;

In cases when the object was moved to the bucket directory not using the myrm tool the "Status" and the "Origin" would be set as "Unknown".

### `myrm show` with `--limit` flag
This command sets the count of items to display per page:

```bash
myrm show --limit 1

Status    Index    Name      Origin                    Removed on
--------  -------  --------  ------------------------  ----------------------
OK              1  test.txt  /home/user_name/test.txt  2022-07-17 10:00:00 AM
```

The default limit value is specified as `10`.

### `myrm show` with `--page` flag
This command sets page to display:

```bash
myrm show --limit 1 --page 1

Status    Index    Name      Origin                    Removed on
--------  -------  --------  ------------------------  ----------------------
OK              1  test.txt  /home/user_name/test.txt  2022-07-17 10:00:00 AM
```

```bash
myrm show --limit 1 --page 2

Status    Index    Name      Origin                    Removed on
--------  -------  --------  ------------------------  ----------------------
OK              2  test      /home/user_name/test      2022-07-17 10:00:00 AM
```

The default shows the first page.

---
### `myrm restore`
This command allows you to restore specified items from the bucket to the original path.
To restore the object, you need to specify its index:

```bash
# Step -- 1.
touch test.txt

# Step -- 2.
myrm rm test.txt

# Step -- 3.
myrm show

Status    Index    Name      Origin                    Removed on
--------  -------  --------  ------------------------  ----------------------
OK              1  test.txt  /home/user_name/test.txt  2022-07-17 10:00:00 AM

# Step -- 4.
myrm restore 1

# Step -- 5.
ls
test.txt

# Step -- 6.
myrm show
2022-07-17--10-00-00 - WARNING :: myrm :: History is empty.
```

> Note: if you specify a non-existent index, the program will display an error message.

```bash
myrm restore 111

2022-07-17--10-00-00 - WARNING :: myrm :: The determined index does not exist in history.
```

---
### `myrm bucket --create`
This command allows you to create a bucket folder if it doesn't exist.

### `myrm bucket --cleanup`
This command allows you to clear the contents of the bucket and its history.

```bash
# Step -- 1.
touch test.txt

# Step -- 2.
myrm rm test.txt

# Step -- 3.
myrm show

Status    Index    Name      Origin                    Removed on
--------  -------  --------  ------------------------  ----------------------
OK              1  test.txt  /home/user_name/test.txt  2022-07-17 10:00:00 AM

# Step -- 4.
myrm bucket --cleanup

# Step -- 5.
myrm show
2022-07-17--10-00-00 - WARNING :: myrm :: History is empty.
```

### `--dry-run` mode
Mode `--dry-run` allows you to run any command from the `myrm` module with `--dry-run` flag.
You can see what happens as a result of executing the command without real changes on the current machine.

```bash
# Step -- 1.
touch test.txt

# Step -- 2.
myrm rm test.txt --dry-run

# Step -- 3.
ls
test.txt

# Step -- 4.
myrm show
2022-07-17--10-00-00 - WARNING :: myrm :: History is empty.
```

---
### `--debug` `--silent` `--verbose` modes
Using these flags with the user command allow set the level of the logging
while executing the user's command:

- `--debug` - print a lot of debugging statements while executing user's commands;
- `--silent` - don't print any statements while executing user's commands;
- `--verbose` - print information statement while executing user's commands;

---
### Settings
The default settings file path is `~/.config/myrm/settings.json`.
This file includes the next bucket configuration:

- Bucket path - the path where bucket will be store on the current machine, by default it is `~/.local/share/myrm/trash_bin`;
- Bucket history path - the path where bucket history will be store on the current machine, by default it is `~/.local/share/myrm/history.pkl`;
- Bucket size - the maximum bucket size in megabytes, by default it equals 100 megabytes;
- Bucket timeout cleanup - the maximum days to store items in bucket on the current machine;

An example settings JSON file:
```json
{
  "bucket_path": "/home/user_name/.local/share/myrm/bucket",
  "bucket_history_path": "/home/user_name/.local/share/myrm/history.pkl",
  "bucket_size": 104857600,
  "bucket_timeout_cleanup": 1728000
}
```

You can change the default settings by creating a new file and replacing the default file with it.

You can also change the defaults settings by using the following flags:
- `--bucket-path`;
- `--bucket-history-path`;
- `--bucket-size`;
- `--bucket-timeout-cleanup`;

---
## Using as a Python library
The main modules:
- `rmlib.py`;
- `bucket.py`;
- `settings.py`;
- `logger.py`;

### rmlib.py
This module allows you to create, move or delete item or group of items on the current machine.
It contains the following functions:

- `rmlib.rm`;
- `rmlib.rmdir`;
- `rmlib.mkdir`;
- `rmlib.mv`;
- `rmlib.mvdir`;

---
#### `rmlib.rm`
This function allows you to permanently delete the specified item from the current machine:

```python
from myrm.rmlib import rm

rm("test.txt")
```

#### `rmlib.rmdir`
This function allows you to permanently delete the specified directory and their contents from the current machine:

```python
from myrm.rmlib import rmdir

rmdir("test")
```

#### `rmlib.mkdir`
This function allows you to create a new directory on the current machine:

```python
from myrm.rmlib import mkdir

mkdir("test")
```

#### `rmlib.mv`
This function allows you to move the specified file from source path to destination path:

```python
from myrm.rmlib import mv

mv("1.txt", "2.txt")
```

#### `rmlib.mvdir`
This function allows you to move the specified directory and their contents from source path to destination path:

```python
from myrm.rmlib import mvdir

mvdir("dir1", "dir2")
```

---
### bucket.py
This module allows you to create the bucket directory.
You can move an item or a group of items to the bucket or delete them permanently from the current machine.
It contains three classes:

- `Status`:
- `Bucket`;
- `BucketHistory`;

___
### `bucket.Status`
This class includes two attributes:

- `CORRECT` - shows the status "OK" if the item was moved to the bucket using the program `myrm`;
- `UNKNOWN` - shows the status "UNKNOWN" if the item was moved to the bucket without using the program `myrm`;

___
### `bucket.Bucket`
This class with built-in methods allows you to create and manage bucket. Also, to save and manage its history.

#### `bucket.Bucket.create`
This built-in method of the class allows you to create the bucket directory on the current machine:

```python
from myrm.bucket import Bucket

bucket = Bucket()
bucket.create()
```

#### `bucket.Bucket.cleanup`
This built-in method of the class allows you to clean up the bucket directory on the current machine:

```python
from myrm.bucket import Bucket

bucket = Bucket()
bucket.cleanup()
```

#### `bucket.Bucket.get_size`
This built-in method of the class allows you to get size of the bucket directory on the current machine:

```python
from myrm.bucket import Bucket

bucket = Bucket()
print(bucket.get_size())
```

#### `bucket.Bucket.rm`
This built-in method of the class allows you to move an item or a group of items to the bucket or delete them permanently from the current machine:

```python
from myrm.bucket import Bucket

bucket = Bucket()
bucket.rm("test.txt")
```

#### `bucket.Bucket.check`
This built-in method of the class allows you to check the contents of the bucket, compare it with the history and delete unnecessary items:

```python
from myrm.bucket import Bucket

bucket = Bucket()
bucket.check()
```

#### `bucket.Bucket.timeout_cleanup`
This built-in method of the class allows you to get the storage time of items in the bucket.
Also, this method deletes items that are stored more than the specified time:

```python
from myrm.bucket import Bucket

bucket = Bucket()
bucket.timeout_cleanup()
```

#### `bucket.Bucket.restore`
This built-in method of the class allows you to restore items from the bucket to their original location on the current machine:

```python
from myrm.bucket import Bucket

bucket = Bucket()
bucket.restore(1)
```

___
### `bucket.BucketHistory`
This class with built-in methods allows you to save and manage bucket history.

#### `bucket.BucketHistory.show`
This built-in method of the class allows you to show a table with items stored in the bucket:

```python
from myrm.bucket import BucketHistory

bucket_history = BucketHistory()
print(bucket_history.show(10, 1))
```

___
### settings.py
This module allows you to generate settings for bucket on the current machine.
It contains the main class and two functions:

- `AppSettings`:
- `generate`;
- `load`;

#### `settins.AppSettings`
This class allows you to create settings.
Also, this class checks the types of data passed to the settings:

```python
from myrm.settings import AppSettings

app_settings = AppSettings()
```

#### `settings.generate`
This function allows you to create json settings file on the current machine:

```python
from myrm.settings import generate

generate()
```

#### `settings.load`
This function allows you to load settings data from the settings file:

```python
from myrm.settings import load

load()
```

___
## License

[MIT](https://choosealicense.com/licenses/mit)
