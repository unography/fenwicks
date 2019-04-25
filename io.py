import tensorflow as tf
import pandas as pd
import random
import os

from typing import List, Tuple
from tqdm import tqdm_notebook as tqdm


def enum_files(data_dir: str, file_ext: str = 'jpg') -> List[str]:
    """
    Enumerate all files with a given extension in a given data directory.

    :param data_dir: Data directory.
    :param file_ext: Extensions of files to enumerate. Default: 'jpg'.
    :return: A list of file names. Note that these are base file names, not full paths.
    """
    file_pattern = os.path.join(data_dir, f'*.{file_ext}')
    matching_files = tf.gfile.Glob(file_pattern)
    return matching_files


# todo: generalize and move to core
def shuffle_paths_labels(paths: List[str], labels: List[int]) -> Tuple[List[str], List[int]]:
    c = list(zip(paths, labels))
    random.shuffle(c)
    paths, labels = zip(*c)
    return list(paths), list(labels)


def find_files(data_dir: str, labels: List[str], shuffle: bool = False, file_ext: str = 'jpg') -> Tuple[
    List[str], List[int]]:
    """
    Find all input files wth a given extension in specific subdirectories of a given data directory. Optionally shuffle
    the found file names.

    :param data_dir: Data directory.
    :param labels: Set of subdirectories (named after labels) in which to find files.
    :param shuffle: Whether to shuffle the outputs.
    :param file_ext: File extension. ONly find files with this extension.
    :return: Two lists: one for file paths and the other for their corresponding labels represented as indexes.
    """
    filepaths = []
    filelabels = []

    for i, label in enumerate(labels):
        matching_files = enum_files(os.path.join(data_dir, label), file_ext)
        filepaths.extend(matching_files)
        filelabels.extend([i] * len(matching_files))

    if shuffle:
        filepaths, filelabels = shuffle_paths_labels(filepaths, filelabels)

    return filepaths, filelabels


def find_files_with_label_csv(data_dir: str, csv_fn: str, shuffle: bool = False, file_ext: str = 'jpg', id_col='id',
                              label_col='label', _labels: List[str] = None) -> Tuple[List[str], List[int], List[str]]:
    train_labels = pd.read_csv(csv_fn)
    labels = sorted(train_labels[label_col].unique()) if _labels is None else _labels
    key_id = dict([(label, idx) for idx, label in enumerate(labels)])

    filepaths = []
    filelabels = []

    for _, row in train_labels.iterrows():
        filepaths.append(os.path.join(data_dir, f'{row[id_col]}.{file_ext}'))
        filelabels.append(key_id[row[label_col]])

    if shuffle:
        filepaths, filelabels = shuffle_paths_labels(filepaths, filelabels)

    return filepaths, filelabels, labels


def find_files_no_label(data_dir: str, shuffle: bool = False, file_ext: str = 'jpg') -> List[str]:
    filepaths = enum_files(data_dir, file_ext)
    if shuffle:
        random.shuffle(filepaths)
    return filepaths


def create_clean_dir(path: str):
    """
    Create a new directory specified by `path`. If this directory already exists, delete all its files and
    subdirectories.

    :param path: Path to the directory to be created or cleaned.
    :return: None
    """
    if tf.gfile.Exists(path):
        tf.gfile.DeleteRecursively(path)
    tf.io.gfile.makedirs(path)


def file_size(fn: str) -> int:
    """
    Get the size of a file in bytes. Works for files on Google Cloud Storage.
    :param fn: Path to the file.
    :return: Size of the file.
    """
    stat = tf.io.gfile.stat(fn)
    return stat.length


def unzip(fn, dest_dir: str = '.', overwrite: bool = False):
    """
    Extract one or more .zip or .7z file(s) to a destination directory.

    :param fn: Name of the file(s) to be decompressed. The type of `fn` can be either `str`, or `List[str]`
    :param dest_dir: Destination directory. Default: current directory.
    :param overwrite: Whether to overwrite when the destination directory already exists. Default: False, in which case
                      nothing is done when the destination directory already exists.
    :return: None.
    """

    try:
        import libarchive.public
    except ImportError:
        raise ImportError('libarchive not installed. Run !apt install libarchive-dev and then !pip install libarchive.')

    is_one_file = isinstance(fn, str)

    if overwrite or not tf.gfile.Exists(dest_dir):
        tf.io.gfile.makedirs(dest_dir)

        if is_one_file:
            files = [os.path.abspath(fn)]
        else:
            files = list(map(os.path.abspath, fn))

        cur_dir = os.getcwd()
        os.chdir(dest_dir)
        for fn in files:
            tf.logging.info(f'Decompressing: {fn}')
            for _ in tqdm(libarchive.public.file_pour(fn)):
                pass
        os.chdir(cur_dir)
    else:
        tf.logging.info(f'Destination directory exists. Skipping.')


def sub_dirs(data_dir: str, exclude_dirs: List[str] = None) -> List[str]:
    """
    List sub directories of a directory, except those excluded. Works for Google Cloud Storage directories.

    :param data_dir: Given directory.
    :param exclude_dirs: names (not full paths) of subdirectories to exclude.
    :return: List of subdirectories' names (not full paths).
    """
    if exclude_dirs is None:
        exclude_dirs = []
    return [path for path in tf.gfile.ListDirectory(data_dir)
            if tf.gfile.IsDirectory(os.path.join(data_dir, path)) and path not in exclude_dirs]


def merge_dirs(source_dirs: List[str], dest_dir: str):
    if not tf.gfile.Exists(dest_dir):
        tf.io.gfile.makedirs(dest_dir)
        for d in source_dirs:
            files = tf.gfile.ListDirectory(d)
            for fn in files:
                old_fn = os.path.join(d, fn)
                new_fn = os.path.join(dest_dir, fn)
                tf.io.gfile.rename(old_fn, new_fn)


def get_model_dir(bucket: str, model: str) -> str:
    """
    Get recommended directory to store parameters of a pre-trained model.

    :param bucket: Google Cloud Storage bucket.
    :param model: Name of the pre-trained model.
    :return: GCS path to store the pre-trained model.
    """
    return os.path.join(os.path.join(bucket, 'model'), model)


def get_gcs_dirs(bucket: str, project: str) -> Tuple[str, str]:
    """
    Get recommended directories for storing datasets (data_dir) and intermediate files generated during training
    (work_dir).

    :param bucket: Google Cloud Storage bucket.
    :param project: Name of the project.
    :return: Data directory for storaing datasets, and work directory for storing intermediate files.
    """
    data_dir = os.path.join(os.path.join(bucket, 'data'), project)
    work_dir = os.path.join(os.path.join(bucket, 'work'), project)
    return data_dir, work_dir


# todo: gcs_path is a dir
def upload_to_gcs(local_path: str, gcs_path: str):
    """
    Upload a local file to Google Cloud Storage, if it doesn't already exist on GCS.

    :param local_path: path to the local file to be uploaded.
    :param gcs_path: path to the GCS file. Need to be the full file name.
    :return: None.
    """
    if not tf.gfile.Exists(gcs_path):
        tf.gfile.Copy(local_path, gcs_path)
    else:
        tf.logging.info('Output file already exists. Skipping.')
