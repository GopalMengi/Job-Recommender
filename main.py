import streamlit as st   # front end
import pymongo  # database connection
from pymongo import MongoClient  # accessing the database url
import pandas as pd  # dataframe operations
import pdfplumber  # visual debugging and data extraction
import PyPDF2  # scan the resume pdf
from rake_nltk import Rake  # keyword extraction algorithm
import string  # string operations
import io  # convert binary resume file into a decoded file that is readable by python
import re  # regular expression
import nltk
import pymongo
import certifi
import ssl
nltk.download('stopwords')
nltk.download('punkt')
import lxml


def keyphrases(file, min_word, max_word, num_phrases):    # extract phrases from the text
    text = file
    text = text.lower()
    text = ''.join(s for s in text if ord(s) > 31 and ord(s) < 126)     # use join function where it joins the characters which fallls in the range specified
    text = text
    text = re.sub(' +', ' ', text)   # replaces multiple spaces with single space
    text = text.translate(str.maketrans('', '', string.punctuation))    # maketrans extracts the punctuations and translate removes the maketrans returned punctuations from the whole text
    text = ''.join([i for i in text if not i.isdigit()])
    r = Rake(min_length=min_word, max_length=max_word)   # input text for the keyword extraction
    r.extract_keywords_from_text(text)    # extract keywords
    phrases = r.get_ranked_phrases()

    if num_phrases < len(phrases):
        phrases = phrases[0:num_phrases]

    return phrases

country = st.sidebar.text_input('Country')               # sidebar interface and input
uploaded_file = st.file_uploader('Upload your resume')   # to upload the function
file_text = ''
phrases = []

if uploaded_file is not None:
    uploaded_file.seek(0)
    file = uploaded_file.read()
    pdf = PyPDF2.PdfFileReader(io.BytesIO(file))      # convert the binary coded file to a python readable file

    for page in range(pdf.getNumPages()):
        file_text += (pdf.getPage(page).extractText())
        phrases.extend(keyphrases(file_text, 2, 4, 10))    # join all the phrases together

if len(phrases) > 0:
    q_terms = st.multiselect('Select key phrases', options=phrases, default=phrases)  # interface of the box



client = pymongo.MongoClient("mongodb+srv://GopalMengi:Gopal_2002@cluster0.ezow6.mongodb.net/companies_sorted?retryWrites=true&w=majority")

def query(country,keywords):

    result = client['companies_sorted']['Companies'].aggregate([
        {
            '$search': {
                'text': {
                    'path': [
                        'industry'
                    ],
                    'query': [
                        ' %s' % (keywords)
                    ],
                    'fuzzy': {
                        'maxEdits': 2,
                        'prefixLength': 2
                    }
                }
            }
        }, {
            '$project': {
                'Name': '$name',
                # 'URL': '$domain',
                'Industry': '$industry',
                # 'University': '$Uni',
                'City': '$locality',
                'Country': '$country',
                'score': {
                    '$meta': 'searchScore'
                }
            }
        }, {
            '$match': {
                'Country': '%s' % (country)
            }
        }, {
            '$limit': 10
        }
    ])

    df = pd.DataFrame(result)

    return df



if st.button('Search'):
    df = query(country,phrases)
    st.write(df)



try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context