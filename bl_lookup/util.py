

class Text:
    """ Utilities for processing text. """

    @staticmethod
    def get_curie (text):
        #Assume it's a string
        return text.upper().split(':', 1)[0] if ':' in text else None

    @staticmethod
    def un_curie (text):
        return ':'.join(text.split (':', 1)[1:]) if ':' in text else text
        
    @staticmethod
    def short (obj, limit=80):
        text = str(obj) if obj else None
        return (text[:min(len(text),limit)] + ('...' if len(text)>limit else '')) if text else None

    @staticmethod
    def path_last (text):
        return text.split ('/')[-1:][0] if '/' in text else text

    @staticmethod
    def obo_to_curie (text):
        return ':'.join( text.split('/')[-1].split('_') )

    @staticmethod
    def opt_to_curie (text):
        if text is None:
            return None
        if text.startswith('http://purl.obolibrary.org') or text.startswith('http://www.orpha.net'):
            return ':'.join( text.split('/')[-1].split('_') )
        if text.startswith('http://linkedlifedata.com/resource/umls'):
            return f'UMLS:{text.split("/")[-1]}'
        if text.startswith('http://identifiers.org/'):
            p = text.split("/")
            return f'{p[-2].upper()}:{p[-1]}'
        return text

    @staticmethod
    def curie_to_obo (text):
        x = text.split(':')
        return f'<http://purl.obolibrary.org/obo/{x[0]}_{x[1]}>'


    @staticmethod
    def snakify(text):
        decomma = '_'.join( text.split(','))
        dedash = '_'.join( decomma.split('-'))
        resu =  '_'.join( dedash.split() )
        return resu

    @staticmethod
    def upper_curie(text):
        if ':' not in text:
            return text
        p = text.split(':', 1)
        return f'{p[0].upper()}:{p[1]}'
