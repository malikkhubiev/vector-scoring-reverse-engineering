def print_header(text, width=100, char="="):
    """Печатает заголовок"""
    print("\n" + char * width)
    print(text)
    print(char * width)

def print_subheader(text, width=80, char="-"):
    """Печатает подзаголовок"""
    print(f"\n{char * width}")
    print(f"🔹 {text}")
    print(char * width)

def print_section(title, content):
    """Печатает секцию с заголовком и содержимым"""
    print(f"\n📌 {title}:")
    print(content)

def print_statistics(stats_dict):
    """Печатает статистику"""
    for key, value in stats_dict.items():
        print(f"   {key}: {value}")