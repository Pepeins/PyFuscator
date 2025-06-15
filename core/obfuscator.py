# -*- coding: utf-8 -*-
import ast
import random
import sys
from pathlib import Path
from .utils import (
    generate_name, xor_string, generate_dummy_code, 
    create_opaque_predicate, create_dead_code_branch,
    encode_string_multilayer, DECODE_FUNCTIONS
)

# Use native ast.unparse if available (Python 3.9+), otherwise fallback
try:
    def unparse_ast(tree):
        return ast.unparse(tree)
except AttributeError:
    try:
        import astunparse
        def unparse_ast(tree):
            return astunparse.unparse(tree)
    except ImportError:
        def unparse_ast(tree):
            raise RuntimeError("Se requiere Python 3.9+ o instalar 'astunparse': pip install astunparse")

class DependencyTracker:
    """Track variable definitions and usage to avoid breaking dependencies"""
    
    def __init__(self):
        self.defined_names = set()
        self.used_names = set()
        self.function_names = set()
        self.class_names = set()
        self.imported_names = set()
        self.global_names = set()
    
    def add_definition(self, name):
        self.defined_names.add(name)
    
    def add_usage(self, name):
        self.used_names.add(name)
    
    def add_function(self, name):
        self.function_names.add(name)
        self.add_definition(name)
    
    def add_class(self, name):
        self.class_names.add(name)
        self.add_definition(name)
    
    def add_import(self, name):
        self.imported_names.add(name)
        self.add_definition(name)
    
    def is_safe_to_obfuscate(self, name):
        """Check if a name is safe to obfuscate without breaking dependencies"""
        # Don't obfuscate if it's used but not defined (external dependency)
        if name in self.used_names and name not in self.defined_names:
            return False
        return True

class ControlFlowFlattener(ast.NodeTransformer):
    def __init__(self):
        self.processed_functions = set()
        
    def flatten_body(self, body, function_name=None):
        # Skip if already processed or body too small
        if (function_name and function_name in self.processed_functions) or len(body) < 4:
            return body

        # Filter valid statements and avoid problematic constructs
        valid_body = []
        for node in body:
            if isinstance(node, ast.stmt):
                # Skip problematic statements that can break flattening
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, 
                                   ast.Try, ast.With, ast.AsyncWith, ast.Global, ast.Nonlocal,
                                   ast.Import, ast.ImportFrom, ast.For, ast.While)):
                    # Don't flatten functions with complex control structures
                    return body
                # Skip f-strings and complex expressions
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.JoinedStr):
                    return body
                else:
                    valid_body.append(node)
        
        if len(valid_body) < 4:  # Need at least 4 statements for meaningful flattening
            return body

        if function_name:
            self.processed_functions.add(function_name)

        try:
            state_var_name = generate_name(prefix="state")
            state_var_load = ast.Name(id=state_var_name, ctx=ast.Load())
            state_var_store = ast.Name(id=state_var_name, ctx=ast.Store())

            # Create blocks with proper state management
            blocks = []
            for i, stmt in enumerate(valid_body):
                block_body = [stmt]
                
                # Handle control flow
                if isinstance(stmt, (ast.Return, ast.Break, ast.Continue)):
                    # Terminal statements
                    next_state = -1
                else:
                    # Normal flow to next statement
                    next_state = i + 1 if i + 1 < len(valid_body) else -1
                
                if next_state != -1:
                    block_body.append(ast.Assign(
                        targets=[state_var_store], 
                        value=ast.Constant(value=next_state)
                    ))
                else:
                    block_body.append(ast.Break())
                
                # Create if block for this state
                condition = ast.Compare(
                    left=state_var_load, 
                    ops=[ast.Eq()], 
                    comparators=[ast.Constant(value=i)]
                )
                
                if i == 0:
                    blocks.append(ast.If(test=condition, body=block_body, orelse=[]))
                else:
                    # Add to elif chain
                    blocks.append(ast.Elif(test=condition, body=block_body, orelse=[]))

            # Build elif chain properly
            main_if = blocks[0]
            current = main_if
            for block in blocks[1:]:
                current.orelse = [block]
                current = block

            # Create main while loop
            while_loop = ast.While(
                test=ast.Compare(
                    left=state_var_load, 
                    ops=[ast.GtE()], 
                    comparators=[ast.Constant(value=0)]
                ),
                body=[main_if],
                orelse=[]
            )

            # Initial state assignment
            init_assign = ast.Assign(
                targets=[state_var_store], 
                value=ast.Constant(value=0)
            )

            return [init_assign, while_loop]
        
        except Exception:
            # If flattening fails, return original body
            return body


class AdvancedObfuscator(ast.NodeTransformer):
    def __init__(self, **kwargs):
        self.options = kwargs
        self.name_map = {}
        self.recursion_depth = 0
        self.max_recursion_depth = 20
        self.cff_applied = set()
        self.errors = []
        self.fstring_count = 0
        self.dependency_tracker = DependencyTracker()
        
        # Extended protected names - more comprehensive
        self.protected_names = {
            # Python builtins and special names
            '__init__', '__main__', '__name__', '__file__', '__doc__', '__dict__',
            '__class__', '__module__', '__qualname__', '__annotations__', '__import__', 
            '__all__', '__author__', '__version__', '__builtins__', '__cached__',
            '__path__', '__package__', '__spec__', '__loader__', '__file__',
            '__enter__', '__exit__', '__iter__', '__next__', '__len__', '__str__',
            '__repr__', '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__',
            '__hash__', '__bool__', '__bytes__', '__format__', '__sizeof__',
            '__getattr__', '__setattr__', '__delattr__', '__getattribute__',
            '__get__', '__set__', '__delete__', '__set_name__',
            '__getitem__', '__setitem__', '__delitem__', '__missing__',
            '__contains__', '__call__', '__new__', '__del__',
            
            # Built-in functions
            'getattr', 'setattr', 'hasattr', 'delattr', 'dir', 'vars', 'globals', 'locals',
            'print', 'input', 'len', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
            'open', 'super', 'isinstance', 'issubclass', 'type', 'id', 'hash',
            'abs', 'min', 'max', 'sum', 'all', 'any', 'pow', 'round', 'divmod',
            'bin', 'oct', 'hex', 'ord', 'chr', 'ascii', 'repr', 'format',
            'compile', 'eval', 'exec', 'memoryview', 'bytearray', 'bytes',
            'frozenset', 'slice', 'complex', 'object', 'property', 'staticmethod',
            'classmethod', 'callable', 'next', 'iter',
            
            # Constants and keywords
            'True', 'False', 'None', 'self', 'cls', 'Ellipsis', 'NotImplemented',
            'Exception', 'BaseException', 'KeyboardInterrupt', 'SystemExit',
            'StopIteration', 'GeneratorExit', 'ArithmeticError', 'LookupError',
            'ValueError', 'TypeError', 'AttributeError', 'NameError', 'IndexError',
            'KeyError', 'ImportError', 'ModuleNotFoundError', 'RuntimeError',
            
            # Language keywords (shouldn't appear as names but just in case)
            'import', 'from', 'as', 'def', 'class', 'if', 'else', 'elif', 'for',
            'while', 'try', 'except', 'finally', 'with', 'return', 'yield', 'raise',
            'break', 'continue', 'pass', 'del', 'and', 'or', 'not', 'in', 'is',
            'lambda', 'global', 'nonlocal', 'assert', 'async', 'await',
            
            # Common standard library names that shouldn't be obfuscated
            'os', 'sys', 'time', 'datetime', 'json', 'math', 'random', 're',
            'urllib', 'http', 'socket', 'threading', 'multiprocessing',
            'pathlib', 'collections', 'itertools', 'functools', 'operator',
            'base64', 'hashlib', 'hmac', 'secrets', 'uuid', 'pickle',
            
            # Our decode functions
            '__decode_xor', '__decode_multilayer', '__DECODING_LAYERS'
        }

    def get_option(self, key, default=False):
        return self.options.get(key, default)

    def visit(self, node):
        if node is None:
            return None
            
        self.recursion_depth += 1
        if self.recursion_depth > self.max_recursion_depth:
            self.recursion_depth -= 1
            return node
        
        try:
            result = super().visit(node)
            if result and hasattr(result, '_fields'):
                ast.fix_missing_locations(result)
            self.recursion_depth -= 1
            return result
        except Exception as e:
            self.errors.append(f"Error processing node {type(node).__name__}: {str(e)}")
            self.recursion_depth -= 1
            return node

    def obfuscate_name(self, name, length=12):
        if (name in self.protected_names or 
            name.startswith('__') and name.endswith('__') or
            name.startswith('_') and len(name) > 10 or  # Likely already obfuscated
            not self.dependency_tracker.is_safe_to_obfuscate(name)):
            return name
            
        if name not in self.name_map:
            self.name_map[name] = generate_name(
                length=length + self.get_option('obfuscation_level', 2)
            )
        return self.name_map[name]

    def visit_JoinedStr(self, node):
        """Handle f-strings - DO NOT obfuscate them to avoid unparse issues"""
        self.fstring_count += 1
        try:
            # Process names inside f-strings carefully
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    if value.value:
                        value.value = self.visit(value.value)
            return node
        except Exception as e:
            self.errors.append(f"F-string processing error: {str(e)}")
            return node

    def visit_FormattedValue(self, node):
        """Handle formatted values inside f-strings"""
        try:
            # Only process simple expressions, avoid complex ones
            if isinstance(node.value, ast.Name):
                # Track usage but don't obfuscate names in f-strings for safety
                self.dependency_tracker.add_usage(node.value.id)
                # Don't obfuscate names inside f-strings to avoid issues
                return node
            elif isinstance(node.value, ast.Attribute):
                node.value = self.visit(node.value)
            return node
        except:
            return node

    def visit_FunctionDef(self, node):
        original_name = node.name
        
        # Track function definition
        self.dependency_tracker.add_function(original_name)
        
        # Obfuscate function name
        if self.get_option('obfuscate_names') and not node.name.startswith('__'):
            node.name = self.obfuscate_name(node.name)
        
        # Obfuscate parameters
        if self.get_option('obfuscate_names'):
            for arg in node.args.args:
                if arg.arg not in self.protected_names:
                    self.dependency_tracker.add_definition(arg.arg)
                    arg.arg = self.obfuscate_name(arg.arg, length=8)
        
        # Process decorators safely
        new_decorators = []
        for decorator in node.decorator_list:
            try:
                processed = self.visit(decorator)
                new_decorators.append(processed)
            except:
                new_decorators.append(decorator)
        node.decorator_list = new_decorators

        # Process function body
        new_body = []
        for stmt in node.body:
            try:
                processed_stmt = self.visit(stmt)
                if isinstance(processed_stmt, list):
                    new_body.extend(processed_stmt)
                elif processed_stmt:
                    new_body.append(processed_stmt)
                else:
                    new_body.append(stmt)  # Fallback to original
                
                # Add dummy code occasionally (but less frequently)
                if (self.get_option('add_dummy_code') and 
                    random.random() < 0.05 and  # Reduced frequency
                    len(new_body) < 30):
                    new_body.append(generate_dummy_code(self.get_option('obfuscation_level')))
            except:
                new_body.append(stmt)  # Keep original if processing fails

        node.body = new_body if new_body else [ast.Pass()]

        # Apply control flow flattening more conservatively
        if (self.get_option('control_flow_flattening') and 
            original_name not in self.cff_applied and
            len(node.body) >= 5 and  # Need more statements
            not any(isinstance(stmt, (ast.ClassDef, ast.FunctionDef, ast.Try, 
                                    ast.AsyncFunctionDef, ast.For, ast.While)) 
                   for stmt in node.body)):
            
            try:
                flattener = ControlFlowFlattener()
                flattened = flattener.flatten_body(node.body, original_name)
                if flattened and len(flattened) > 0 and len(flattened) != len(node.body):
                    node.body = flattened
                    self.cff_applied.add(original_name)
            except Exception as e:
                self.errors.append(f"CFF failed for function {original_name}: {str(e)}")
        
        # Add dead code branch less frequently
        if (self.get_option('dead_code_insertion') and 
            random.random() < 0.1 and  # Reduced frequency
            len(node.body) < 20):
            try:
                dead_branch = create_dead_code_branch()
                insert_pos = random.randint(0, len(node.body))
                node.body.insert(insert_pos, dead_branch)
            except:
                pass  # Skip if fails
        
        return node

    def visit_ClassDef(self, node):
        original_name = node.name
        
        # Track class definition
        self.dependency_tracker.add_class(original_name)
        
        if self.get_option('obfuscate_names') and not node.name.startswith('__'):
            node.name = self.obfuscate_name(node.name)
        
        try:
            self.generic_visit(node)
        except:
            pass  # Keep original if processing fails
        return node

    def visit_Name(self, node):
        # Track name usage/definition
        if isinstance(node.ctx, ast.Store):
            self.dependency_tracker.add_definition(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.dependency_tracker.add_usage(node.id)
        
        if (self.get_option('obfuscate_names') and 
            isinstance(node.ctx, (ast.Store, ast.Load)) and
            not node.id.startswith('__')):
            node.id = self.obfuscate_name(node.id)
        return node

    def is_string_safe_to_obfuscate(self, string_value):
        """Enhanced string safety check"""
        if not string_value or not isinstance(string_value, str):
            return False
            
        # Skip very short or very long strings
        if len(string_value) <= 2 or len(string_value) > 200:  # Reduced max length
            return False
            
        # Skip whitespace-only strings
        if string_value.isspace():
            return False
            
        # Skip dunder strings
        if string_value.startswith('__') and string_value.endswith('__'):
            return False
            
        # Skip import-related strings
        if any(string_value.startswith(prefix) for prefix in ['import ', 'from ', '__']):
            return False
            
        # Skip format strings and common patterns that might break
        dangerous_patterns = [
            '{', '}',  # Format strings
            '\\n', '\\t', '\\r',  # Escape sequences
            '%s', '%d', '%f', '%r', '%c',  # Old-style format strings
            'utf-8', 'ascii', 'latin-1', 'cp1252',  # Encodings
            'http://', 'https://', 'ftp://', 'file://',  # URLs
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',  # SQL
            'class ', 'def ', 'if ', 'for ', 'while ',  # Code patterns
            '#!/', '#coding', '# -*- coding',  # Shebang and encoding
        ]
        
        for pattern in dangerous_patterns:
            if pattern in string_value:
                return False
        
        # Skip strings that look like file paths
        if any(char in string_value for char in ['/', '\\', '.']):
            if len(string_value.split('.')) > 1 or len(string_value.split('/')) > 1:
                return False
                
        return True

    def visit_Constant(self, node):
        # String obfuscation with enhanced safety checks
        if (self.get_option('obfuscate_strings') and 
            isinstance(node.value, str) and 
            self.is_string_safe_to_obfuscate(node.value)):
            
            try:
                if self.get_option('string_encryption'):
                    return encode_string_multilayer(node.value)
                else:
                    encoded, key = xor_string(node.value)
                    return ast.Call(
                        func=ast.Name(id='__decode_xor', ctx=ast.Load()),
                        args=[ast.Constant(value=encoded), ast.Constant(value=key)],
                        keywords=[]
                    )
            except Exception as e:
                self.errors.append(f"String obfuscation failed for '{node.value[:20]}...': {str(e)}")
                return node

        # Number obfuscation with safety limits
        if (self.get_option('obfuscate_numbers') and 
            isinstance(node.value, int) and 
            10 <= abs(node.value) <= 1000):  # More conservative range
            
            try:
                op_choice = random.randint(0, 1)  # Reduced complexity
                if op_choice == 0:  # Addition/subtraction
                    offset = random.randint(50, 200)
                    return ast.BinOp(
                        left=ast.Constant(value=node.value + offset), 
                        op=ast.Sub(), 
                        right=ast.Constant(value=offset)
                    )
                else:  # XOR
                    key = random.randint(50, 200)
                    return ast.BinOp(
                        left=ast.Constant(value=node.value ^ key), 
                        op=ast.Xor(), 
                        right=ast.Constant(value=key)
                    )
            except:
                return node
        
        return node

    def visit_If(self, node):
        if self.get_option('opaque_predicates') and random.random() < 0.2:  # Reduced frequency
            try:
                always_true_pred = create_opaque_predicate(always_true=True)
                node.test = ast.BoolOp(
                    op=ast.And(), 
                    values=[always_true_pred, self.visit(node.test)]
                )
                
                # Add dead code in else branch less frequently
                if not node.orelse and random.random() < 0.1:
                    node.orelse = [create_dead_code_branch()]
            except:
                pass  # Skip if fails
        
        try:
            self.generic_visit(node)
        except:
            pass
        return node

    def visit_Import(self, node):
        # Track imported names
        for alias in node.names:
            target_name = alias.asname or alias.name.split('.')[-1]
            self.dependency_tracker.add_import(target_name)
        
        # Be more conservative with import obfuscation
        if not self.get_option('obfuscate_names') or self.get_option('obfuscation_level') < 3:
            return node
        
        try:
            new_nodes = []
            for alias in node.names:
                module_name = alias.name
                target_name = alias.asname or module_name.split('.')[-1]

                # Skip critical system modules
                if module_name in ['sys', 'os', 'builtins', '__main__', 'ast', 'astunparse',
                                 'json', 'time', 're', 'math', 'random', 'base64']:
                    return node

                try:
                    obfuscated_module_str = encode_string_multilayer(module_name)
                    
                    import_call = ast.Call(
                        func=ast.Name(id='__import__', ctx=ast.Load()),
                        args=[obfuscated_module_str],
                        keywords=[]
                    )
                    
                    assign_node = ast.Assign(
                        targets=[ast.Name(id=self.obfuscate_name(target_name), ctx=ast.Store())],
                        value=import_call
                    )
                    new_nodes.append(assign_node)
                except:
                    # If obfuscation fails, keep original import
                    return node
            
            return new_nodes if new_nodes else node
        except:
            return node

    def visit_ImportFrom(self, node):
        # Track imported names
        for alias in node.names:
            target_name = alias.asname or alias.name
            self.dependency_tracker.add_import(target_name)
        
        # Be more conservative with import obfuscation
        if not self.get_option('obfuscate_names') or not node.module or self.get_option('obfuscation_level') < 3:
            return node
        
        try:
            # Skip critical system modules
            if node.module in ['sys', 'os', 'builtins', '__main__', 'ast', 'astunparse',
                             'json', 'time', 're', 'math', 'random', 'base64']:
                return node
                
            new_nodes = []
            module_name = node.module
            
            try:
                obfuscated_module_str = encode_string_multilayer(module_name)
                
                from_list = [ast.Constant(value=alias.name) for alias in node.names]
                import_call = ast.Call(
                    func=ast.Name(id='__import__', ctx=ast.Load()),
                    args=[
                        obfuscated_module_str, 
                        ast.Constant(value=None), 
                        ast.Constant(value=None), 
                        ast.List(elts=from_list, ctx=ast.Load())
                    ],
                    keywords=[]
                )
                
                temp_module_var = generate_name(prefix="mod")
                new_nodes.append(ast.Assign(
                    targets=[ast.Name(id=temp_module_var, ctx=ast.Store())], 
                    value=import_call
                ))

                for alias in node.names:
                    name_to_import = alias.name
                    target_name = alias.asname or name_to_import

                    obfuscated_name_str = encode_string_multilayer(name_to_import)

                    getattr_call = ast.Call(
                        func=ast.Name(id='getattr', ctx=ast.Load()),
                        args=[
                            ast.Name(id=temp_module_var, ctx=ast.Load()), 
                            obfuscated_name_str
                        ],
                        keywords=[]
                    )
                    
                    assign_node = ast.Assign(
                        targets=[ast.Name(id=self.obfuscate_name(target_name), ctx=ast.Store())],
                        value=getattr_call
                    )
                    new_nodes.append(assign_node)

                return new_nodes if new_nodes else node
            except:
                return node
        except:
            return node


class PyObfuscator:
    def __init__(self, **kwargs):
        self.options = kwargs

    def _create_decode_functions(self):
        functions_code = []
        imports = "import base64\nimport random\n\n"
       
        if self.options.get('obfuscate_strings', False):
            if self.options.get('string_encryption', False):
                functions_code.append(DECODE_FUNCTIONS['__decode_multilayer'])
            else:
                functions_code.append(DECODE_FUNCTIONS['__decode_xor'])

        if not functions_code:
            return ""

        return imports + "\n".join(functions_code) + "\n"

    def validate_generated_code(self, code):
        """Basic validation of generated code"""
        try:
            # Try to parse the generated code
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error in generated code: {e}"
        except Exception as e:
            return False, f"Error validating generated code: {e}"

    def obfuscate_file(self, input_path, output_path):
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Read file with multiple encoding attempts
        source = None
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(input_path, "r", encoding=encoding) as f:
                    source = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if source is None:
            raise ValueError(f"No se pudo leer el archivo {input_path.name} con ninguna codificación")
        
        # Parse AST
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Error de sintaxis en {input_path.name}: {e}")
        
        # Apply obfuscation
        obfuscator = AdvancedObfuscator(**self.options)
        
        try:
            obfuscated_tree = obfuscator.visit(tree)
            ast.fix_missing_locations(obfuscated_tree)
        except Exception as e:
            raise RuntimeError(f"Error durante la ofuscación: {e}")

        # Generate obfuscated code
        try:
            obfuscated_code = unparse_ast(obfuscated_tree)
        except Exception as e:
            error_msg = f"Error al generar código ofuscado: {str(e)}"
            if "fstring" in str(e).lower() or "joinedstr" in str(e).lower():
                error_msg += f"\nProblema con f-strings (encontradas: {obfuscator.fstring_count}). "
                error_msg += "El archivo contiene f-strings complejas que no se pueden ofuscar."
                error_msg += "\nSugerencia: Usa strings normales con .format() en lugar de f-strings."
            elif "unparser" in str(e).lower():
                error_msg += f"\nProblema con el unparsing. Python version: {sys.version}"
                if sys.version_info < (3, 9):
                    error_msg += "\nInstala astunparse: pip install astunparse"
            raise RuntimeError(error_msg)
        
        # Add decode functions
        decode_helpers = self._create_decode_functions()
        final_code = decode_helpers + obfuscated_code
        
        # Validate the generated code
        is_valid, validation_error = self.validate_generated_code(final_code)
        if not is_valid:
            raise RuntimeError(f"El código generado contiene errores: {validation_error}")
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_code)
        
        # Return any errors encountered
        errors = obfuscator.errors
        if obfuscator.dependency_tracker.used_names - obfuscator.dependency_tracker.defined_names:
            undefined_names = obfuscator.dependency_tracker.used_names - obfuscator.dependency_tracker.defined_names
            # Filter out built-ins and protected names
            undefined_names = undefined_names - obfuscator.protected_names
            if undefined_names:
                errors.append(f"Posibles nombres indefinidos después de la ofuscación: {', '.join(undefined_names)}")
        
        return errors