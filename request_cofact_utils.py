
# An example to get the remaining rate limit using the Github GraphQL API.
import requests

url = 'https://cofacts-api.g0v.tw/graphql'


def run_query(query, number): # A simple function to use requests.post to make the API call. Note the json= section.
    query = insert_query_term(query, number)
    request = requests.post(url, json={'query': query})
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

def insert_query_term(query, number): # A simple function to use requests.post to make the API call. Note the json= section.
    query = '"' + str(query) +'"'
    query_template = """
    query{
    ListArticles(
        filter:{
            moreLikeThis:{
                like:"""+query+"""
            }
            replyCount:{
                GT: """+str(1)+"""
            }
        }
        first:"""+str(number)+"""
    ){
        edges{
        node{
            text
            hyperlinks{
            url
            }
        articleReplies{
            reply{
            text
            type
            }
        }
        }
        }
        
    }
    }
    """

    return query_template

        
# The GraphQL query (with a few aditional bits included) itself defined as a multi-line string.       

