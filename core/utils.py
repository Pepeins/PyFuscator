# -*- coding: utf-8 -*-
import ast
import base64
import random
import string

def generate_name(length=12, prefix=""):
    # More conservative character selection to avoid encoding issues
    confusing_chars = "Il1O0"
    # Reduced unicode chars to avoid potential issues
    unicode_chars = "αβγδεζηθικλμνξοπρστυφχψω"
    
    base_chars = string.ascii_letters + string.digits
    population = base_chars + confusing_chars
    
    # Add unicode chars only occasionally
    if random.random() < 0.3:
        population += unicode_chars
    
    name = ''.join(random.choices(population, k=length))
    
    # Ensure it starts with a valid character
    if not name[0].isalpha() and name[0] != '_':
        name = random.choice(string.ascii_letters + '_') + name[1:]
    
    reserved_endings = ['__', '_builtin', '_module', '_class']
    for ending in reserved_endings:
        if name.endswith(ending):
            name = name[:-len(ending)] + generate_name(length=3)
    
    return prefix + name

def xor_string(s: str):
    if not s:
        return s, ""
    
    if len(s) > 200:
        return s, ""
        
    try:
        key = ''.join(random.choices(
            string.ascii_letters + string.digits, 
            k=random.randint(8, 16)
        ))
        
        encoded = []
        for i, char in enumerate(s):
            key_c = key[i % len(key)]
            try:
                encoded_c = chr(ord(char) ^ ord(key_c))
                # Avoid null characters and other problematic chars
                if ord(encoded_c) < 32 or ord(encoded_c) > 126:
                    return s, ""  # Return original if encoding produces problematic chars
                encoded.append(encoded_c)
            except (ValueError, OverflowError):
                return s, ""  # Return original if encoding fails
        
        return ''.join(encoded), key
    except Exception:
        return s, ""

# Multi-layer encoding functions
def _encode_b64(s): 
    try:
        if len(s) > 100:  # Limit length
            return s
        return base64.b64encode(s.encode('utf-8')).decode('ascii')
    except Exception:
        return s

def _decode_b64(s): 
    try:
        return base64.b64decode(s).decode('utf-8')
    except Exception:
        return s

def _encode_rot(s): 
    try:
        if len(s) > 100:  # Limit length
            return s
        return ''.join(chr((ord(c) + 13) % 256) for c in s)
    except Exception:
        return s

def _decode_rot(s): 
    try:
        return ''.join(chr((ord(c) - 13 + 256) % 256) for c in s)
    except Exception:
        return s

def _encode_reverse(s): 
    try:
        return s[::-1]
    except Exception:
        return s

def _decode_reverse(s): 
    try:
        return s[::-1]
    except Exception:
        return s

def _encode_hex(s): 
    try:
        if len(s) > 50:  # Limit length for hex encoding
            return s
        return s.encode('utf-8').hex()
    except Exception:
        return s

def _decode_hex(s): 
    try:
        return bytes.fromhex(s).decode('utf-8')
    except Exception:
        return s

ENCODING_LAYERS = [
    (0, _encode_b64),
    (1, _encode_rot),
    (2, _encode_reverse),
    (3, _encode_hex)
]

def encode_string_multilayer(s: str):
    if not s or len(s) > 100:  # More conservative length limit
        return ast.Constant(value=s)
        
    encoded = s
    applied_layers_indices = []
    
    try:
        layers_to_apply = list(range(len(ENCODING_LAYERS)))
        random.shuffle(layers_to_apply)
        num_layers = random.randint(1, 2)  # Fewer layers to reduce complexity
        
        for i in range(num_layers):
            layer_idx = layers_to_apply[i]
            func = ENCODING_LAYERS[layer_idx][1]
            new_encoded = func(encoded)
            
            # Verify encoding worked and didn't make string too long
            if new_encoded and new_encoded != encoded and len(new_encoded) < 500:
                encoded = new_encoded
                applied_layers_indices.append(layer_idx)
            else:
                break
                
        if not applied_layers_indices:
            return ast.Constant(value=s)
            
        return ast.Call(
            func=ast.Name(id='__decode_multilayer', ctx=ast.Load()),
            args=[
                ast.Constant(value=encoded),
                ast.List(elts=[ast.Constant(value=i) for i in applied_layers_indices], ctx=ast.Load())
            ],
            keywords=[]
        )
    except Exception:
        return ast.Constant(value=s)

# Enhanced decode functions with better error handling
DECODE_FUNCTIONS = {
    '__decode_xor': """
def __decode_xor(data, key):
    if not data or not key:
        return data
    try:
        return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))
    except (ValueError, TypeError, IndexError):
        return data
""",
    '__decode_multilayer': """
def __safe_b64_decode(s):
    try:
        return __import__('base64').b64decode(s.encode('ascii')).decode('utf-8') if s else s
    except Exception:
        return s

def __safe_rot_decode(s):
    try:
        return ''.join(chr((ord(c) - 13 + 256) % 256) for c in s) if s else s
    except Exception:
        return s

def __safe_reverse(s):
    try:
        return s[::-1] if s else s
    except Exception:
        return s

def __safe_hex_decode(s):
    try:
        return bytes.fromhex(s).decode('utf-8') if s else s
    except Exception:
        return s

__DECODING_LAYERS = {
    0: __safe_b64_decode,
    1: __safe_rot_decode,
    2: __safe_reverse,
    3: __safe_hex_decode
}

def __decode_multilayer(data, layers):
    if not data or not layers:
        return data
    try:
        decoded = data
        for layer_idx in reversed(layers):
            if layer_idx in __DECODING_LAYERS:
                decoded = __DECODING_LAYERS[layer_idx](decoded)
                if not decoded:  # If decoding fails, return original
                    return data
        return decoded
    except Exception:
        return data
"""
}

# Opaque predicates
def create_opaque_predicate(always_true=True):
    """Create mathematically provable true/false conditions"""
    x = random.randint(5, 50)  # Smaller range to avoid overflow
    y = random.randint(5, 50)
    
    if always_true:
        predicates = [
            # Mathematical identities that are always true
            ast.Compare(
                left=ast.BinOp(left=ast.Constant(x), op=ast.Add(), right=ast.Constant(0)),
                ops=[ast.Eq()], 
                comparators=[ast.Constant(x)]
            ),
            # Length is always >= 0
            ast.Compare(
                left=ast.Call(func=ast.Name(id='len', ctx=ast.Load()), 
                             args=[ast.Constant("x")], keywords=[]),
                ops=[ast.GtE()], 
                comparators=[ast.Constant(0)]
            ),
            # Simple arithmetic identity
            ast.Compare(
                left=ast.BinOp(left=ast.Constant(x * 2), op=ast.FloorDiv(), right=ast.Constant(2)),
                ops=[ast.Eq()], 
                comparators=[ast.Constant(x)]
            ),
        ]
    else:  # always_false
        predicates = [
            # Even number cannot equal odd number
            ast.Compare(
                left=ast.Constant(x * 2),
                ops=[ast.Eq()], 
                comparators=[ast.Constant(x * 2 + 1)]
            ),
            # Positive number cannot be negative
            ast.Compare(
                left=ast.Constant(abs(x)),
                ops=[ast.Lt()], 
                comparators=[ast.Constant(0)]
            ),
        ]
    
    return random.choice(predicates)

# Dead code generation
def create_dead_code_branch():
    var1 = generate_name(6, prefix="dead")
    
    return ast.If(
        test=create_opaque_predicate(always_true=False),
        body=[
            ast.Assign(
                targets=[ast.Name(id=var1, ctx=ast.Store())], 
                value=ast.Constant(random.randint(100, 999))
            ),
        ],
        orelse=[]
    )

def generate_dummy_code(level=2):
    if level <= 1:
        # Simple assignment
        var_name = generate_name(6, prefix="dummy")
        return ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())], 
            value=ast.Constant(random.randint(1, 100))
        )
    else:
        # Simple loop with basic operation
        var_name = generate_name(8, prefix="dummy")
        loop_var = generate_name(2, prefix="i")
        
        return ast.For(
            target=ast.Name(id=loop_var, ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Name(id='range', ctx=ast.Load()), 
                args=[ast.Constant(random.randint(1, 3))],  # Very small range
                keywords=[]
            ),
            body=[
                ast.Assign(
                    targets=[ast.Name(id=var_name, ctx=ast.Store())],
                    value=ast.BinOp(
                        left=ast.Constant(random.randint(10, 50)),
                        op=ast.Add(),  # Only addition to be safe
                        right=ast.Constant(random.randint(1, 5))
                    )
                )
            ],
            orelse=[]
        )
