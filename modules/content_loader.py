from langchain_community.document_loaders import WebBaseLoader
import bs4

# 본문 크롤링 
def get_article_content(url):

    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                "div",
                attrs={"class": ["newsct_article _article_body", "media_end_head_title"]}
            )
        )
    )
    
    try:
        return loader.load()
            
    except Exception as e:
        print(f"본문 추출 실패: {url}\n사유: {e}")
        return None
