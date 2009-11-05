// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

class formatted_string_buffer
{
public:
	formatted_string_buffer()
	{
		_dynamic_buffer = 0;
		_len = 0;
	}

	formatted_string_buffer(const char *fmt, ...)
	{
		va_list args;
		va_start(args, fmt);
		_dynamic_buffer = 0;
		format(fmt, args);
	}

	formatted_string_buffer(const char *fmt, void *args)
	{
		_dynamic_buffer = 0;
		format(fmt, args);
	}
	
	~formatted_string_buffer()
	{
		memory_deallocate(_dynamic_buffer);
	}

	int format( const char *fmt, ... )
	{
		va_list args;
		va_start(args, fmt);
		_dynamic_buffer = 0;
		
		return format(fmt, args);
	}

	int format(const char *fmt, va_list args)
	{
		if(_dynamic_buffer)
		{
			memory_deallocate(_dynamic_buffer);
			_dynamic_buffer = 0;
		}
		
		_len = vsnprintf(_fixed_buffer, sizeof(_fixed_buffer), fmt, args);
		if(_len < sizeof(_fixed_buffer))
			return _len;
		
		_dynamic_size = sizeof(_fixed_buffer);
		for(;;)
		{
			_dynamic_size *= 2;
			_dynamic_buffer = (char *) memory_reallocate(_dynamic_buffer, _dynamic_size, false);
			_len = vsnprintf(_dynamic_buffer, _dynamic_size, fmt, args);
			if(_len < _dynamic_size)
			{
				// trim off the remainder of the allocation
				memory_reallocate(_dynamic_buffer, _len + 1, true);
				return _len;
			}
		}
	}

	bool copy(char *buffer, uint buffer_size)
	{
		assert(buffer_size > 0);
		if(buffer_size >= size())
		{
			memcpy(buffer, c_str(), size());
			return true;
		}
		else
		{
			memcpy(buffer, c_str(), buffer_size - 1);
			buffer[buffer_size - 1] = 0;
			return false;
		}
	}

	uint length() { return _len; };

	uint size() { return _len + 1; };

	const char* c_str()
	{
		return _dynamic_buffer ? _dynamic_buffer : _fixed_buffer;
	}

	static int format_buffer(char *buffer, uint buffer_size, const char *fmt, ...)
	{
		va_list args;
		va_start(args, fmt);
		return format_buffer(buffer, buffer_size, fmt, args);
	}
		
	static int format_buffer(char *buffer, uint buffer_size, const char *fmt, va_list args)
	{
		assert(buffer_size > 0);
		int len = vsnprintf(buffer, buffer_size, fmt, args);
		buffer[buffer_size - 1] = 0;
		return len;
	}
private:
	char  _fixed_buffer[2048]; // Fixed size buffer
	char* _dynamic_buffer; // Format buffer for strings longer than _fixed_buffer
	uint _dynamic_size; // Size of dynamic buffer
	uint _len; // Length of the formatted string
};
