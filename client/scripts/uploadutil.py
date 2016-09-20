import ziputil, ue4util
# Use python to upload files to server

def upload_s3(bucket_name, filename):
    '''
    Upload file to Amazon S3 server
    '''
    import boto
    from filechunkio import FileChunkIO
    # From http://boto.cloudhackers.com/en/latest/s3_tut.html
    # from boto.s3.connection import S3Connection
    S3_ACCESS_KEY = os.environ['AWS_ACCESS_KEY_ID']
    S3_SECRET_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    # conn = S3Connection(S3_ACCESS_KEY, S3_SECRET_KEY)
    print S3_ACCESS_KEY
    print S3_SECRET_KEY

    # Connect to S3
    c = boto.connect_s3(host='s3-ap-northeast-1.amazonaws.com')
    # c = boto.connect_s3(host='s3-us-west-1.amazonaws.com')
    b = c.get_bucket(bucket_name)

    # Get file info
    source_path = filename
    source_size = os.stat(source_path).st_size

    # Create a multipart upload request
    mp = b.initiate_multipart_upload(os.path.basename(source_path))

    # Use a chunk size of 50 MiB (feel free to change this)
    chunk_size = 52428800
    chunk_count = int(math.ceil(source_size / float(chunk_size)))

    # Send the file parts, using FileChunkIO to create a file-like object
    # that points to a certain byte range within the original file. We
    # set bytes to never exceed the original file size.
    for i in range(chunk_count):
        print 'Uploading chunk %d/%d' % (i, chunk_count)
        offset = chunk_size * i
        bytes_to_send = min(chunk_size, source_size - offset)
        with FileChunkIO(source_path, 'r', offset=offset,
                             bytes=bytes_to_send) as fp:
            mp.upload_part_from_file(fp, part_num=i + 1)

    # Finish the upload
    mp.complete_upload()

def upload_scp(remote, files, local_root, password=None, key_filename=None, DEBUG=False):
    '''
    Local root will be subtracted from the abspath of files
    '''
    import os, paramiko

    # Make sure the remote is with a correct format
    if '@' in remote:
        [username, remain] = remote.split('@')
    else:
        remain = remote
        username = None

    [host, remote_root] = remain.split(':')

    absfiles = ziputil.get_all_files(files, include_folder=True)
    local_root = ue4util.get_real_abspath(local_root) + ue4util.get_path_sep()
    if DEBUG:
        print 'Local root is %s' % repr(local_root)
        print 'Remote root is %s' % repr(remote_root)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.load_system_host_keys()
    # ssh.load_host_keys(os.path.expanduser(os.path.join('~', '.ssh', 'known_hosts')))
    # ssh.connect(scp_conf['Host'], username = scp_conf['Username'], password = scp_conf['Password'])

    ssh.load_system_host_keys()
    # ssh.connect(scp_conf['Host'])

    ssh.connect(host, username = username, password = password, key_filename = key_filename)
    # Use private key for authentication
    # remote_root = scp_conf['RemoteRoot']

    sftp = ssh.open_sftp()

    # client = scp.Client(host = scp_conf['host'], user = scp_conf['user'], password = scp_conf['password'])
    for local_filename in absfiles:
        if not local_root in local_filename:
            exit('The local_root %s is not found is the abs filename %s' % (repr(local_root), repr(local_filename)))
        relative_filename = local_filename.replace(local_root, '')
        # print 'local filename: %s, relative filename: %s' % (local_filename, relative_filename)

        if os.path.isdir(local_filename):
            # remote_dir = os.path.join(remote_root, relative_filename)
            remote_dir = '/'.join([remote_root, relative_filename]) # Make sure we use '/' here
            if DEBUG:
                print 'Mkdir remote dir %s' % repr(remote_dir)

            try:
                sftp.mkdir(remote_dir)
            except:
                pass # maybe exist
            continue
        else:
            # remote_filename = os.path.join(remote_root, relative_filename)
            remote_filename = '/'.join([remote_root, relative_filename])
            if DEBUG:
                print '%s -> %s' % (repr(local_filename), repr(remote_filename))
            # client.transfer(filename, remote_filename)
            sftp.put(local_filename, remote_filename)

    sftp.close()
    ssh.close()

if __name__ == '__main__':
    # Run test
    upload_scp("pyupload.py")
