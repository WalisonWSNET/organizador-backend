from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import re
import dateutil.parser
from dateutil.relativedelta import relativedelta
import spacy

# Classe para processamento de linguagem natural para datas
class NaturalLanguageProcessor:
    def __init__(self):
        # Expressões regulares para datas comuns em português
        self.date_patterns = {
            'amanha': r'amanh[ãa]',
            'hoje': r'hoje',
            'proxima_semana': r'(pr[óo]xima\s+semana)|(semana\s+que\s+vem)',
            'dias_especificos': r'(segunda|ter[çc]a|quarta|quinta|sexta|s[áa]bado|domingo)(\s*-feira)?',
            'em_x_dias': r'(em|daqui\s+a)\s+(\d+)\s+dias?',
            'data_especifica': r'(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?',
            'hora_especifica': r'(\d{1,2})[h:](\d{0,2})(?:\s*(am|pm|AM|PM))?'
        }
        
        # Mapeamento de dias da semana
        self.weekdays = {
            'segunda': 0, 'segunda-feira': 0, 
            'terca': 1, 'terça': 1, 'terça-feira': 1, 'terca-feira': 1,
            'quarta': 2, 'quarta-feira': 2, 
            'quinta': 3, 'quinta-feira': 3, 
            'sexta': 4, 'sexta-feira': 4, 
            'sabado': 5, 'sábado': 5, 
            'domingo': 6
        }
        
        # Carregar modelo spaCy para português (se disponível)
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except:
            # Fallback para modelo em inglês se o português não estiver disponível
            self.nlp = spacy.load("en_core_web_sm")
    
    def extract_date_from_text(self, text):
        """
        Extrai data e hora de um texto em linguagem natural
        Retorna um objeto datetime ou None se não encontrar
        """
        now = datetime.now()
        text = text.lower()
        
        # Verificar padrões de data
        # Amanhã
        if re.search(self.date_patterns['amanha'], text):
            target_date = now + timedelta(days=1)
        
        # Hoje
        elif re.search(self.date_patterns['hoje'], text):
            target_date = now
        
        # Próxima semana
        elif re.search(self.date_patterns['proxima_semana'], text):
            target_date = now + timedelta(days=7)
        
        # Em X dias
        elif match := re.search(self.date_patterns['em_x_dias'], text):
            days = int(match.group(2))
            target_date = now + timedelta(days=days)
        
        # Dias específicos (segunda, terça, etc.)
        elif match := re.search(self.date_patterns['dias_especificos'], text):
            day_name = match.group(1).lower()
            if day_name in self.weekdays:
                target_weekday = self.weekdays[day_name]
                days_ahead = (target_weekday - now.weekday()) % 7
                if days_ahead == 0:  # Se for o mesmo dia da semana, vai para a próxima semana
                    days_ahead = 7
                target_date = now + timedelta(days=days_ahead)
            else:
                target_date = now
        
        # Data específica (DD/MM/YYYY)
        elif match := re.search(self.date_patterns['data_especifica'], text):
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else now.year
            
            # Ajustar ano se for formato de dois dígitos
            if year < 100:
                year += 2000
                
            try:
                target_date = datetime(year, month, day)
                # Se a data já passou este ano, assumir próximo ano
                if target_date < now and match.group(3) is None:
                    target_date = datetime(now.year + 1, month, day)
            except ValueError:
                # Data inválida
                target_date = now
        else:
            # Nenhum padrão encontrado
            target_date = now
        
        # Extrair hora se presente
        if match := re.search(self.date_patterns['hora_especifica'], text):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            
            # Ajustar para formato 24h se AM/PM estiver presente
            if match.group(3) and match.group(3).lower() == 'pm' and hour < 12:
                hour += 12
            elif match.group(3) and match.group(3).lower() == 'am' and hour == 12:
                hour = 0
                
            target_date = target_date.replace(hour=hour, minute=minute)
        else:
            # Se não houver hora específica, definir para 9:00
            target_date = target_date.replace(hour=9, minute=0)
        
        return target_date
    
    def extract_task_info(self, text):
        """
        Extrai informações da tarefa a partir do texto
        Retorna um dicionário com título e data
        """
        # Extrair data
        due_date = self.extract_date_from_text(text)
        
        # Usar o texto original como título da tarefa
        title = text
        
        return {
            'title': title,
            'due_date': due_date
        }
