"""
Función print segura que no falla si stdout/stderr están cerrados
"""
import sys
import io


def safe_print(*args, **kwargs):
    """
    Versión segura de print que no falla si stdout está cerrado
    
    Args:
        *args: Argumentos para print
        **kwargs: Keyword arguments para print (file, sep, end, etc.)
    """
    # Usar __builtins__ para evitar recursión
    import builtins
    _original_print = builtins.print
    
    try:
        # Verificar si el archivo de salida está cerrado
        if 'file' in kwargs:
            file = kwargs['file']
        else:
            file = sys.stdout
        
        # Si el archivo está cerrado, cambiar a stderr
        if hasattr(file, 'closed') and file.closed:
            file = sys.stderr
            kwargs['file'] = file
        
        # Si stderr también está cerrado, usar un buffer
        if hasattr(file, 'closed') and file.closed:
            # Crear un buffer temporal y simplemente ignorar
            buffer = io.StringIO()
            sep = kwargs.get('sep', ' ')
            end = kwargs.get('end', '\n')
            buffer.write(sep.join(str(arg) for arg in args) + end)
            # No hacer nada más, solo evitar el error
            return
        
        # Intentar print normal
        _original_print(*args, **kwargs)
    except (ValueError, IOError, OSError, AttributeError) as e:
        # Si falla, intentar escribir directamente
        try:
            if 'file' in kwargs:
                file = kwargs['file']
            else:
                file = sys.stderr  # Cambiar a stderr como fallback
            
            # Verificar que no esté cerrado
            if hasattr(file, 'closed') and file.closed:
                # Si está cerrado, usar buffer
                buffer = io.StringIO()
                sep = kwargs.get('sep', ' ')
                end = kwargs.get('end', '\n')
                buffer.write(sep.join(str(arg) for arg in args) + end)
                return
            
            # Intentar escribir directamente
            sep = kwargs.get('sep', ' ')
            end = kwargs.get('end', '\n')
            file.write(sep.join(str(arg) for arg in args) + end)
            if hasattr(file, 'flush'):
                file.flush()
        except Exception:
            # Si todo falla, simplemente ignorar
            pass


def safe_print_error(*args, **kwargs):
    """Versión segura de print para errores (usa stderr)"""
    kwargs['file'] = sys.stderr
    safe_print(*args, **kwargs)

