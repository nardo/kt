// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

class page_allocator
{
public:
	enum {
		alignment = 4,
		page_size = 16384,
	};
	page_allocator()
	{
		_current_offset = page_size;
		_current_page_size = page_size;
		
		_current_page = 0;
	}

	~page_allocator()
	{
		clear();
	}
	
	virtual void clear()
	{
		while(_current_page)
		{
			page *prev = _current_page->prev;
			memory_deallocate(_current_page);
			_current_page = prev;
		}	
	}
	
	void *allocate(uint size)
	{
		if(!size)
			return 0;

		// align size:
		size = (size + (alignment - 1)) & ~(alignment - 1);
		
		if(_current_offset + size > _current_page_size)
		{
			uint new_size = size + page_header_size;
			if(new_size < page_size)
				new_size = page_size;
							
			page *new_page = (page *) memory_allocate(new_size);
			new_page->allocator = this;
			uint new_offset = page_header_size + size;
			
			new_page->prev = _current_page;
			_current_page = new_page;
			_current_page_size = new_size;
			_current_offset = new_offset;

			return ((char *) new_page) + page_header_size;
		}
		else
		{
			void *ret = ((char *) _current_page) + _current_offset;
			_current_offset += size;
			return ret;
		}
	}
private:
	struct page
	{
		page_allocator *allocator;
		page *prev;
	};
	uint _current_offset;
	uint _current_page_size;
	page *_current_page;
	uint _alignment;
	
public:
	enum {
		page_header_size = (sizeof(page) + (alignment - 1)) & ~(alignment - 1),
	};
};
