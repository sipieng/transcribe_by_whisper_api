from openai import OpenAI
from config import AI_CONFIG

def process_text(text_content):
    """
    使用AI处理文本内容
    
    Args:
        text_content: 转录得到的文本内容
    
    Returns:
        str: AI处理后的文本
    """
    try:
        client = OpenAI(
            base_url=AI_CONFIG["base_url"],
            api_key=AI_CONFIG["api_key"]
        )
        
        response = client.chat.completions.create(
            model=AI_CONFIG["model"],
            messages=[
                {"role": "user", "content": AI_CONFIG["system_prompt"] + text_content},
            ]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"AI处理文本时出错: {str(e)}")
        # 如果处理失败，返回原文
        return text_content


if __name__ == "__main__":
    # 测试用例
    test_text = """
    In December 1992, a tailback of second-hand Toyota Corollas, Ford Escorts and Fiat Mirafioris, the cars of a middle-income country, snaked its way from a supermarket car park in Northern Ireland to the border of the Irish Republic. On the northern side, bemused British soldiers patrolling their watchtowers weren't sure what was going on. The Irish police, the Gardaí, on the southern side, knew fine well what the story was. Some of their colleagues were in the queue. It was Christmas, booze was cheaper in Northern Ireland than in the Republic of Ireland, Irish people like to drink and December is party time. The queues this year were longer than usual. Traditionally, the booze arbitrage was exploited by people close to the border. But in 1992, thousands more were desperate to spend their Irish punts. We were witnessing a run on a currency triggered by rumours of an imminent devaluation. Spooked, people wanted to spend and buying beer was a way for ordinary people to hedge exchange rate risk. Buy cheap British beer today, with the expense of Irish money, before it too becomes cheap. There is no more damning vote of no confidence in a currency than your own people rushing for the exit. A currency collapse proceeds in stages. Initially, it's bankers, financiers and speculators who become fidgety. By the time teachers, nurses, police officers and plumbers are trying to stock up on cheap booze, it's all over.
    """
    print(process_text(test_text))