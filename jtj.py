import getopt
import sys
import json
import os
from datetime import datetime, date, time
from typing import Dict, Any, Set, List

def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])

def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase"""
    components = snake_str.split('_')
    return ''.join(word.capitalize() for word in components)

def date_valid(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except:
        return False
    return True

def datetime_valid(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except:
        return False
    return True

def time_valid(value: str) -> bool:
    try:
        time.fromisoformat(value)
    except:
        return False
    return True

def get_java_type(value: Any, field_name: str = "") -> str:
    """Determine Java type from Python value"""
    if value is None:
        return "String"  # Default for null values
    elif date_valid(value):
        return "LocalDate"
    elif time_valid(value):
        return "LocalTime"
    elif datetime_valid(value):
        return "LocalDateTime"
    elif isinstance(value, bool):
        return "Boolean"
    elif isinstance(value, int):
        return "Integer"
    elif isinstance(value, float):
        return "Double"
    elif isinstance(value, str):
        return "String"
    elif isinstance(value, list):
        if len(value) == 0:
            return "List<String>"  # Default for empty arrays
        # Check the first element to determine list type
        first_element = value[0]
        if isinstance(first_element, dict):
            # Create class name from field name
            class_name = to_pascal_case(field_name.rstrip('s'))  # Remove plural 's'
            return f"List<{class_name}>"
        else:
            element_type = get_java_type(first_element)
            return f"List<{element_type}>"
    elif isinstance(value, dict):
        # For nested objects, use PascalCase of field name
        return to_pascal_case(field_name)
    else:
        return "String"  # Fallback

def analyze_json_structure(data: Any, class_name: str = "Root") -> Dict[str, Dict]:
    """Analyze JSON structure and identify all classes needed"""
    classes = {}
    
    def analyze_object(obj: Dict, current_class_name: str):
        if current_class_name not in classes:
            classes[current_class_name] = {}
        
        for key, value in obj.items():
            java_field_name = to_camel_case(key)
            java_type = get_java_type(value, key)
            
            classes[current_class_name][java_field_name] = {
                'type': java_type,
                'original_name': key
            }
            
            # Recursively analyze nested objects
            if isinstance(value, dict) and value:  # Non-empty dict
                nested_class_name = to_pascal_case(key)
                analyze_object(value, nested_class_name)
            elif isinstance(value, list) and value:  # Non-empty list
                first_element = value[0]
                if isinstance(first_element, dict):
                    nested_class_name = to_pascal_case(key.rstrip('s'))  # Remove plural 's'
                    analyze_object(first_element, nested_class_name)
                    # Analyze all elements to get complete field set
                    for item in value[1:]:
                        if isinstance(item, dict):
                            analyze_object(item, nested_class_name)
    
    if isinstance(data, dict):
        analyze_object(data, class_name)
    elif isinstance(data, list) and data:
        # If root is an array, analyze the first element
        first_element = data[0]
        if isinstance(first_element, dict):
            analyze_object(first_element, class_name)
            # Analyze all elements to get complete field set
            for item in data[1:]:
                if isinstance(item, dict):
                    analyze_object(item, class_name)
    
    return classes

def generate_java_class(class_name: str, fields: Dict, access_modifier: str, package_name: str = "com.example.model", generate_getters: bool = False, generate_setters: bool = False) -> str:
    """Generate Java class code"""
    imports = set()
    
    # Determine necessary imports
    for field_info in fields.values():
        field_type = field_info['type']
        if field_type.startswith('List<'):
            imports.add("import java.util.List;")
        if 'LocalDate' == field_type:
            imports.add("import java.time.LocalDate;")
        if 'LocalTime' == field_type:
            imports.add("import java.time.LocalTime;")
        if 'LocalDateTime' == field_type:
            imports.add("import java.time.LocalDateTime;")
    
    # Add Jackson annotations import
    imports.add("import com.fasterxml.jackson.annotation.JsonProperty;")
    
    # Generate class
    code = f"package {package_name};\n\n"
    
    # Add imports
    for imp in sorted(imports):
        code += imp + "\n"

    code += "\n/**\n"
    code += " * This class is generated by the JSON to Java Class Generator.\n"
    code += " */\n"
    
    code += "public class " + class_name + " {\n"
    
    # Generate fields
    for java_field_name, field_info in fields.items():
        field_type = field_info['type']
        original_name = field_info['original_name']
        
        if access_modifier:
            code += f"    @JsonProperty(access = JsonProperty.Access.{access_modifier}, value = \"{original_name}\")\n"
        else:
            code += f"    @JsonProperty(value = \"{original_name}\")\n"
        code += f"    private {field_type} {java_field_name};\n\n"
    
    # Generate getters and setters only if requested
    if generate_getters or generate_setters:
        for java_field_name, field_info in fields.items():
            field_type = field_info['type']
            capitalized_field = java_field_name.capitalize()
            
            if generate_getters:
                code += f"    public {field_type} get{capitalized_field}() {{\n"
                code += f"        return {java_field_name};\n"
                code += f"    }}\n\n"
            
            if generate_setters:
                code += f"    public void set{capitalized_field}({field_type} {java_field_name}) {{\n"
                code += f"        this.{java_field_name} = {java_field_name};\n"
                code += f"    }}\n\n"
    
    code += "}\n"
    return code

def create_output_directory(output_path: str) -> str:
    """Create output directory and return the full path"""
    if os.path.isdir(output_path):
        return output_path
    else:
        # If it's a file path, create directory structure
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        return directory if directory else "."

def main():
    args = sys.argv[1:]
    options = "hi:o:p:a:gs"
    long_options = ["help", "input=", "output=", "package=", "access=", "getters", "setters"]
    
    input_file = None
    output_path = "generated"
    package_name = "com.example.model"
    access_modifier = None
    generate_getters = False
    generate_setters = False
    
    try:
        arguments, values = getopt.getopt(args, options, long_options)
    except getopt.error as err:
        print(str(err), file=sys.stderr)
        print_help()
        sys.exit(2)
    
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--help"):
            print_help()
            sys.exit()
        elif current_argument in ("-i", "--input"):
            input_file = current_value
        elif current_argument in ("-o", "--output"):
            output_path = current_value
        elif current_argument in ("-p", "--package"):
            package_name = current_value
        elif current_argument in ("-a", "--access"):
            access_modifier = current_value
        elif current_argument in ("-g", "--getters"):
            generate_getters = True
        elif current_argument in ("-s", "--setters"):
            generate_setters = True
    
    if access_modifier not in ["READ_ONLY", "WRITE_ONLY", "READ_WRITE", "AUTO", None]:
        print("Error: Invalid access modifier", file=sys.stderr)
        print_help()
        sys.exit(1)

    if not input_file:
        print("Error: Input file is required", file=sys.stderr)
        print_help()
        sys.exit(1)
    
    try:
        # Read and parse JSON
        with open(input_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Analyze JSON structure
        print(f"Analyzing JSON structure from {input_file}...")
        
        # Determine root class name from filename
        root_class_name = os.path.splitext(os.path.basename(input_file))[0]
        root_class_name = to_pascal_case(root_class_name.replace('-', '_').replace(' ', '_'))
        
        classes = analyze_json_structure(data, root_class_name)
        
        print(f"Found {len(classes)} classes to generate:")
        for class_name in classes.keys():
            print(f"  - {class_name}")
        
        # Create output directory
        output_dir = create_output_directory(output_path)
        
        # Generate Java classes
        generated_files = []
        for class_name, fields in classes.items():
            java_code = generate_java_class(class_name, fields, access_modifier, package_name, generate_getters, generate_setters)
            
            # Write to file
            output_file = os.path.join(output_dir, f"{class_name}.java")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(java_code)
            
            generated_files.append(output_file)
            print(f"Generated: {output_file}")
        
        print(f"\nSuccessfully generated {len(generated_files)} Java classes in '{output_dir}'")
        print(f"Package: {package_name}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def print_help():
    print("JSON to Java Class Generator")
    print("https://github.com/Kecerim24/JsonToJackson")
    print()
    print("Usage: python main.py -i <input_file> [-o <output_path>] [-p <package_name>] [-a <access_modifier>] [-g] [-s]")
    print()
    print("Options:")
    print("  -h, --help              Show this help message and exit")
    print("  -i, --input <file>      Input JSON file (required)")
    print("  -o, --output <path>     Output directory or file path (default: 'generated')")
    print("  -p, --package <name>    Java package name (default: 'com.example.model')")
    print("  -a, --access <name>     Jackson access modifier (options: READ_ONLY, WRITE_ONLY, READ_WRITE, AUTO)")
    print("  -g, --getters           Generate getters (default: False)")
    print("  -s, --setters           Generate setters (default: False)")
    print()
    print("Examples:")
    print("  python main.py -i data.json")
    print("  python main.py -i data.json -o src/main/java/com/mycompany/model")
    print("  python main.py -i data.json -o generated/ -p com.mycompany.dto -a READ_WRITE")
    print("  python main.py -i data.json -g  # Generate with getters")
    print("  python main.py -i data.json -s  # Generate with setters")

if __name__ == "__main__":
    main()
