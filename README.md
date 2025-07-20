```markdown
# PyObfuscator 🐍🔒

Python code obfuscator with multiple protection techniques including control flow flattening, string encryption, and smart name scrambling.

## 🚀 Features

- **🔤 String Encryption** - Multi-layer encoding with XOR and Base64
- **🏷️ Name Scrambling** - Variables, functions, and classes obfuscation  
- **🔀 Control Flow Flattening** - Restructure program logic
- **🧩 Opaque Predicates** - Insert mathematical puzzles
- **💀 Dead Code Injection** - Add unreachable branches
- **🛡️ Smart Protection** - Preserves imports and critical functions

## 📦 Installation

```bash
git clone https://github.com/Pepeins/PyObuscator.git
cd PyFuscator
python install_dependencies.py
python main.py
```

## 💡 Usage

1. Place Python files in `~/Desktop/pyfuscator/input/`
2. Run the tool and select obfuscation level
3. Get protected files from `~/Desktop/pyfuscator/output/`

### Obfuscation Levels
- **🟢 Basic** - Fast, essential protection
- **🟡 Intermediate** - Balanced security/performance
- **🔴 Advanced** - Maximum protection (ts is test)

## 📝 Example

**Original:**
```python
def calculate(value, factor=2):
    result = value * factor
    return result
```

**Obfuscated:**
```python
import base64
import random


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
                if not decoded: 
                    return data
        return decoded
    except Exception:
        return data

def cTd1v0oRMpkTIwV(χrOηsRλo0Ps, F2Hq4yQWLg0=2):
    Kln3φcax6NFDψIT = χrOηsRλo0Ps * F2Hq4yQWLg0
    return Kln3φcax6NFDψIT
```

## ⚠️ Notes

- This is a only beta test
- Test obfuscated code before deployment
- Complex f-strings may need conversion to `.format()`
- Requires Python 3.7+ and `astunparse` for older versions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or report issues.

## ⭐ Support

If you find this tool useful, please give it a star ⭐ and share it with others!
```
