// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

class file
{
	int _file_descriptor;
	public:
	
	file() { _file_descriptor = -1; }
	~file() { close(); }
	uint get_position()
	{
		if(_file_descriptor == -1)
			return 0;
		return lseek(_file_descriptor, 0, SEEK_CUR);
	}
	
	void set_position(uint position)
	{
		if(_file_descriptor != -1)
			lseek(_file_descriptor, off_t(position), SEEK_SET);
	}
	
	uint get_size()
	{
		if(_file_descriptor == -1)
			return 0;
	
		off_t current_position = lseek(_file_descriptor, 0, SEEK_CUR);
		off_t file_size = lseek(_file_descriptor, 0, SEEK_END);
		lseek(_file_descriptor, current_position, SEEK_SET);
		return uint(file_size);
	}
	void close()
	{
		if(_file_descriptor == -1)
		{
			::close(_file_descriptor);
			_file_descriptor = -1;
		}
	}
	
	bool read(void *buffer, uint num_bytes, size_t *bytes_actually_read = 0)
	{
		if(_file_descriptor == -1)
		{
			if(bytes_actually_read)
			*bytes_actually_read = 0;
			return false;
		}
		if(!num_bytes)
			return true;
		
		ssize_t elements_read = ::read(_file_descriptor, buffer, num_bytes);
		if(bytes_actually_read != 0)
			*bytes_actually_read = elements_read;
		
		return elements_read == num_bytes;
	}
	
	bool write(const void *buffer, uint num_bytes)
	{
		if(_file_descriptor == -1)
			return false;
		if(!num_bytes)
			return true;
		return ::write(_file_descriptor, buffer, num_bytes) == num_bytes;
	}
	
	enum open_mode
	{
		open_read,
		open_write_truncate,
		open_write_append,
		open_read_write,
	};
	
	enum result_code
	{
		success,
		permission_denied,
		no_such_file,
		quota_reached,
		directory_opened_for_write,
		read_only_filesystem,
		default_error,
	};

	static bool open(file &the_stream, const char *path, open_mode the_mode, result_code *result = 0)
	{
		the_stream.close();
		
		int open_flag = 0;
		switch(the_mode)
		{
		case open_read:
			open_flag |= O_RDONLY;
			break;
		case open_write_truncate:
			open_flag |= O_WRONLY | O_CREAT | O_TRUNC;
			break;
		case open_write_append:
			open_flag |= O_WRONLY | O_CREAT | O_APPEND;
			break;
		case open_read_write:
			open_flag |= O_RDWR | O_CREAT;
			break;
		}
		const mode_t default_permissions = S_IRUSR | S_IWUSR; // default permissions are read/write for owner only.
		int file_descriptor;
		if(open_flag & O_CREAT)
			file_descriptor = ::open(path, open_flag, default_permissions);
		else
			file_descriptor = ::open(path, open_flag);
		
		if(file_descriptor != -1)
		{
			the_stream._file_descriptor = file_descriptor;
			if(result)
				*result = success;
			return true;
		}
		if(result)
		{
			switch(errno)
			{
			case EACCES:
				*result = permission_denied;
				break;
			case EDQUOT:
				*result = quota_reached;
				break;
			case EISDIR:
				*result = directory_opened_for_write;
				break;
			case ENOENT:
				*result = no_such_file;
				break;
			case EROFS:
				*result = read_only_filesystem;
				break;
			default:
				*result = default_error;
				break;
			}
		}
		return false;
	}
	
	static bool remove(const char *path, result_code *result = 0)
	{
		int unlink_result = unlink(path);
		if(!result)
			return unlink_result == 0 ? true : false;
		if(unlink_result == 0)
		{
			*result = success;
			return true;
		}
		switch(errno)
		{
		case EACCES:
		case EPERM:
			*result = permission_denied;
			break;
		case ENOENT:
			*result = no_such_file;
			break;
		case EROFS:
			*result = read_only_filesystem;
			break;
		}
		return false;
	}
};


static void file_test()
{
	printf("---- file class unit test ----\n");
	const char *test_file_path = "file_test.txt";
	file the_file;
	file::result_code the_code;
	if(!file::open(the_file, test_file_path, file::open_write_truncate, &the_code))
	{
		printf("Failed to create test file -- error = %d\n", the_code);
		return;
	}
	// write some data into the file:
	const char *data_string = "This is a test string... wooooooooot.";
	the_file.write(data_string, strlen(data_string));
	the_file.close();
	
	if(!file::open(the_file, "file_test.txt", file::open_read, &the_code))
	{
		printf("Failed to open test file -- error = %d\n", the_code);
		return;
	}
	
	uint file_size = the_file.get_size();
	char *read_buffer = new char[file_size + 1];
	
	the_file.read(read_buffer, file_size);
	read_buffer[file_size] = 0;
	
	if(strcmp(read_buffer, data_string))
	{
		printf("Failed: data read inconsistent.\n");
		return;
	}
	the_file.close();
	if(!file::remove(test_file_path, &the_code))
	{
		printf("Failed to remove test file -- error = %d\n", the_code);
		return;
	}
	printf("file test succeeded.\n");
}