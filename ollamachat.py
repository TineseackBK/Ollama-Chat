import streamlit as st
import streamlit_authenticator as stauth
import ollama
import csv
import json
import os
import datetime

# 配置
st.set_page_config(
    page_title= 'Ollama Chat'
)

# 样式
st.markdown("""
    <style>
    .dashed-box {
        border: 2px dashed #FFA500;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --------------------------------

# session 初始化
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'model_option' not in st.session_state:
    st.session_state.model_option = None

if 'style_option' not in st.session_state:
    st.session_state.style_option = None

if 'ai_avatar' not in st.session_state:
    st.session_state.ai_avatar = None

if 'user_avatar' not in st.session_state:
    st.session_state.user_avatar = None

if 'history' not in st.session_state:
    st.session_state.history = []

# --------------------------------

# 登录与注册
def _login():
    st.title('Ollama Chat')
    with st.form('login'):
        st.title('用户登录')
        username = st.text_input('用户名', value='')
        password = st.text_input('密码', value='', type='password')
        submit = st.form_submit_button('登录', use_container_width=True)

        # 检查密码
        flag = False
        with open('./users/accounts.csv', 'r') as f:
            reader = csv.reader(f)

            for row in reader:
                usn = row[0]
                pwd = row[1]
                if username == usn:
                    if password == pwd:
                        flag = True
                        break
                    else:
                        flag = False

        if submit:
            # 登录成功
            if flag == True:
                st.session_state.current_username = username
                st.success('登录成功，正在跳转页面...')
                st.session_state.logged_in = True
                _load_the_history()
                # 刷新页面
                st.rerun()
            # 登录失败
            else:
                st.error('用户名或密码错误')
                
    with st.form('register'):
        st.title('用户注册')
        username = st.text_input('用户名', value='')
        password = st.text_input('密码', value='')
        password_c = st.text_input('确认密码', value='')
        submit = st.form_submit_button('注册', use_container_width=True)

        # 查重
        flag = True
        with open('./users/accounts.csv', 'r') as f:
            reader = csv.reader(f)

            for row in reader:
                usn = row[0]
                if username == usn:
                    flag = False

        if submit:
            # 没有重复用户名
            if flag == True:
                # 注册成功
                if password == password_c:
                    # 存数据
                    with open('./users/accounts.csv', 'a', encoding='utf-8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([username, password])

                    st.session_state.current_username = username
                    st.success('注册成功，正在跳转页面...')
                    st.session_state.logged_in = True
                    _load_the_history()
                    # 刷新页面
                    st.rerun()
                # 注册失败
                else:
                    st.error('两次输入的密码不同，请检查密码')
            # 重复用户名
            else:
                st.error('用户名已存在')

# 退出登录
def _logout():
    st.session_state.logged_in = False
    
    # 缓存聊天记录
    _cache_the_history()

# --------------------------------

# 导出聊天记录
def _export_the_history():    
    nowtime = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

    if not os.path.isdir("./outputs/logs"):
        os.makedirs("./outputs/logs")
    with open(f"./outputs/logs/history_{nowtime}.json", "w", encoding='utf-8') as f:
        json.dump([history_message for history_message in st.session_state.history], f, ensure_ascii=False, indent=4)

# 登录时自动导入聊天记录和配置
def _load_the_history():
    # 清除当前 st.session_state.history
    st.session_state.history = []

    # 根据当前的用户名，导入聊天记录
    # 如果不存在聊天记录，则跳过
    try:
        with open(f"./cache/logs/history_{st.session_state.current_username}.json", "r", encoding='utf-8') as f:
            st.session_state.history = json.load(f)
    except FileNotFoundError:
        pass

    # 根据当前的用户名，加载配置
    # 如果不存在配置，则初始化 session
    try:
        with open(f"./cache/user_settings/user_{st.session_state.current_username}.csv", "r", encoding='utf-8') as f:
            reader = csv.reader(f)
            first_row = next(reader)
            st.session_state.model_option = first_row[0]
            st.session_state.style_option = first_row[1]
            st.session_state.ai_avatar = first_row[2]
            st.session_state.user_avatar = first_row[3]
    except FileNotFoundError:
        st.session_state.model_option = None
        st.session_state.style_option = None
        st.session_state.ai_avatar = None
        st.session_state.user_avatar = None

# 退出登录时自动缓存聊天记录和配置
def _cache_the_history():
    if not os.path.isdir("./cache/logs"):
        os.makedirs("./cache/logs")
    if not os.path.isdir("./cache/user_settings"):
        os.makedirs("./cache/user_settings")

    with open(f"./cache/logs/history_{st.session_state.current_username}.json", "w", encoding='utf-8') as f:
        json.dump([history_message for history_message in st.session_state.history], f, ensure_ascii=False, indent=4)
    with open(f"./cache/user_settings/user_{st.session_state.current_username}.csv", "w", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([choose_model, ai_style, ai_config_avatar, user_config_avatar])        

# 清空聊天记录
def _clear_the_history():
    st.session_state.history = []

# 应用自定义 AI 风格
def _set_ai_style():
    if ai_style == '默认':
        style_changed_reply = ollama.chat(
            model = choose_model,
            messages = [{
                'role': 'system',
                'content': '你好！'
            }]
        )
    elif ai_style == '（自定义）':
        style_changed_reply = ollama.chat(
            model = choose_model,
            messages = [{
                'role': 'system',
                'content': ai_style_customize
            }]
        )
    else:
        style_changed_reply = ollama.chat(
            model = choose_model,
            messages = [{
                'role': 'system',
                'content': f'您是一位{ai_style}。'
            }]
        )

    _answer = style_changed_reply['message']['content']

    # 在页面上显示 AI 的回答
    with st.chat_message("assistant", avatar=ai_config_avatar):
        st.markdown(_answer)

    # 保存 AI 的回答到聊天记录中
    st.session_state.history.append({'role': 'assistant', 'content': _answer})

# 调试函数
def _debug_function():
    pass

# --------------------------------

# 侧边栏
if st.session_state.logged_in:
    with st.sidebar:
        # 用户名显示
        st.title(f'欢迎您，{st.session_state.current_username}')

        # 切换模型
        models = [
                'yi',
                'llama3:8b',
            ]

        choose_model = st.selectbox(
            '切换模型',
            models,
            index=models.index(st.session_state.model_option) if st.session_state.model_option else 0
        )

        # 自定义 AI 风格
        styles = [
                '默认',
                '（自定义）',
                '老师',
                '厨师',
                '医生',
                '警察',
                '音乐家',
                '艺术家',
                '软件工程师',
                '摄影师'
            ]
        
        ai_style = st.selectbox(
            '选择AI风格',
            styles,
            index=styles.index(st.session_state.style_option) if st.session_state.style_option else 0
        )

        ai_style_customize = st.text_area(
            '输入自定义AI风格',
            placeholder='如“您是一位消防员。”'
        )

        ai_style_button = st.button('应用', on_click=_set_ai_style, use_container_width=True)

        # 分割线
        st.write('---------------------------')

        # 设置头像
        avatars = [
            '🤖', '🚗', '🚲', '🚇', '🕍', '🌚', '🌝','😺', '🐶', '🐺', '🦁', '🐯', '🦊', '🐷', '🐮', '🐭', '🐻', '🐸', '🐽', '🐔', '🦄', '🐉', '🐟', '🦜', '🐧', '🐝'
        ]

        ai_config_avatar = st.selectbox(
            'AI 头像',
            avatars,
            index=avatars.index(st.session_state.ai_avatar) if st.session_state.ai_avatar else 0
        )

        user_config_avatar = st.selectbox(
            '用户头像',
            avatars,
            index=avatars.index(st.session_state.user_avatar) if st.session_state.user_avatar else 7
        )

        # 分割线
        st.write('---------------------------')

        # 聊天记录保存
        save_button = st.button('导出聊天记录', on_click=_export_the_history, use_container_width=True)

        # 退出登录
        logout_button = st.button('退出登录', on_click=_logout, use_container_width=True)

        # 清空聊天记录
        clear_button = st.button('清空聊天记录', on_click=_clear_the_history, use_container_width=True)

        # 调试按钮
        # debug_button = st.button('调试某些东西', on_click=_debug_function, use_container_width=True)

# --------------------------------

# 显示历史信息
if st.session_state.logged_in:
    for history_message in st.session_state.history:
        if history_message["role"] == 'user':
            with st.chat_message(history_message["role"], avatar=user_config_avatar):
                st.markdown(history_message["content"])
        else:
            with st.chat_message(history_message["role"], avatar=ai_config_avatar):
                st.markdown(history_message["content"])

# 用户点击发送
if st.session_state.logged_in:
    if user_input := st.chat_input("发送信息: "):
        # 在页面上显示用户的消息
        with st.chat_message("user", avatar=user_config_avatar):
            st.markdown(user_input)

        # 保存用户的消息到聊天记录中
        st.session_state.history.append({'role': 'user', 'content': user_input})       

        # 构建输入（已更新为全部的对话记录后 40 条作为输入）、处理回答
        response = ollama.chat(
            model = choose_model,
            messages = st.session_state.history[-40:],
            stream = False
        )
        answer = response['message']['content']

        # 在页面上显示 AI 的回答
        with st.chat_message("assistant", avatar=ai_config_avatar):
            st.markdown(answer)

        # 保存 AI 的回答到聊天记录中
        st.session_state.history.append({'role': 'assistant', 'content': answer})

else:
    # 如果用户未登录，则显示登录页面
    _login()