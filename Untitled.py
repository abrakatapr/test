#!/usr/bin/env python
# coding: utf-8

# # Задание 1
# вам выгружены два вида файлов
# -Все скачивания приложения (сырые данные) (нужное событие: install)
# -Фродовые скачивания приложений (ботовые пользователи)-отчет агрегированный (нужное событие: Total fraudulent attribution) 
# 
# 1)Объедини каждый вид файлов, чтобы получить все данные
# 2) по источникам (Media source) рассчитай  кол-во скачиваний всего и кол-во фродовых скачиваний, выведи процентное содержание форда по источникам
# 3)каждому обычному инсталлу присвой цену 0,5$(наша прибыль), каждому фродовому  -0,2$(рекламодатель вычитает у нас)
# 3) выведи Топ-5 источников по фродовым скачиваниям (отдельно с самым высоким процентом и самым низким процентом)
# 4) выведи суммарно сколько денег мы заработали, сколько заплатили за фрод и разницу между ними(итоговый заработок=прибыль-вычет)
# 5)выведи Топ-5 источников с самым высоким содержанием фрода, сколько суммарно мы заплатили за этот фрод и какой процент от всего фрода составляют эти 5 источников
# 

# In[1]:


import pandas as pd
import numpy as np


# In[2]:


df1 = pd.read_csv('id1072084799_installs_2024-01-15_2024-01-31_Asia_Nicosia.csv')
df2 = pd.read_csv('id1072084799_installs_2024-02-01_2024-02-05_Asia_Nicosia.csv')


# In[3]:


df3 = pd.read_csv('protect360_report.csv', header=1)
df4 = pd.read_csv('protect360_report-3.csv', header=1)


# ## 1)Объедини каждый вид файлов, чтобы получить все данные

# In[4]:


df1.info()


# In[5]:


df2.info()


# In[6]:


df2['Media Source'].head()


# In[7]:


df3.info()


# In[8]:


df4.info()


# In[9]:


df_inst = pd.concat([df1,df2], ignore_index = True)


# In[10]:


#тут позже сгруппирую и просуммирую по источникам
df_fraud = pd.concat([df3,df4], ignore_index = True)


# In[11]:


df_inst.info()


# In[12]:


df_fraud.info()


# **Column 'Total fraudulent attribution' - object**

# In[13]:


df_fraud.columns


# In[14]:


df_fraud['Total fraudulent attribution\n        '].unique()


# In[15]:


#избавляюсь от неразрывного пробела
df_fraud['Total fraudulent attribution\n        '] = (
    df_fraud['Total fraudulent attribution\n        ']
    .apply(lambda x: str(x).replace(u'\xa0', u''))
    .astype({'Total fraudulent attribution\n        ':'int64'})
)


# ## 2) по источникам (Media source) рассчитай  кол-во скачиваний всего и кол-во фродовых скачиваний, выведи процентное содержание фрода по источникам

# In[16]:


df_grouped_inst = (
    df_inst.groupby(['Media Source'])
    .count()['Install Time']
#to_frame чтобы использовать источник как индекс
    .to_frame('Installs').reset_index()
    .set_index('Media Source'))


# In[17]:


df_grouped_fraud = (
    df_fraud[['Unnamed: 0','Total fraudulent attribution\n        ']]
    .rename(
        columns={'Unnamed: 0':'Media Source','Total fraudulent attribution\n        ':'Fraud Installs'}
    )
)
df_grouped_fraud = (
    df_grouped_fraud.groupby(['Media Source'])
    .sum()['Fraud Installs']
    .to_frame('Fraud Installs')
    .reset_index()
    .set_index('Media Source')
)


# In[18]:


df = (
    pd.merge(
        df_grouped_fraud,
        df_grouped_inst,
        left_index=True,
        right_index=True,
        how='outer'
    ).fillna(0)
)
#после мержа установки становятся флоат. исправлю это
df['Installs'] = df['Installs'].astype('int64')


# In[19]:


df['Fraud to All'] = round(df['Fraud Installs'] / df['Installs'],2)
df


# In[20]:


df['Fraud to All'] = df['Fraud to All'].replace([np.inf, np.NaN], [1.00, 0])


# In[21]:


df['Fraud to All'].max()


# Явно какая-то ошибка. Не может быть фродовых скачиваний больше, чем всех скачиваний. Так как нет понимания источника ошибки, то я уберу все строки с этими ошибками

# In[22]:


df = df.loc[df['Fraud Installs'] <= df['Installs']]


# In[23]:


print('Процентное содержание фрода по всем источникам =', round(df['Fraud Installs'].sum() / df['Installs'].sum() * 100,2),'%')


# In[24]:


(df['Fraud to All'] *100).astype(str).head(15) +'%'


# ## 3) Каждому обычному инсталлу присвой цену 0,5\\$(наша прибыль), каждому фродовому  -0,2\\$(рекламодатель вычитает у нас)

# In[25]:


pay_inst, pay_fraud = [0.5,-0.2]


# ## 4) Выведи Топ-5 источников по фродовым скачиваниям (отдельно с самым высоким процентом и самым низким процентом)

# Это не ответ

# In[26]:


df.sort_values(by = ['Fraud Installs'], ascending=False).head()


# In[27]:


df.sort_values(by = ['Fraud to All', 'Fraud Installs'], ascending=False).head()


# In[28]:


df.loc[df['Fraud to All'] == 1].sort_values(by = ['Fraud Installs'], ascending=False)


# In[29]:


print(len(df.loc[df['Fraud to All'] == 1]), 'источников, у которых только фродовые скачивания')


# Избавлюсь от них, занеся в отдельный список

# In[30]:


ban_list = df.index.to_list()


# In[31]:


df = df.drop(df.loc[df['Fraud to All'] == 1].index)


# Также избавлюсь от незначительных источников, количество скачивания с которых меньше среднего
# 
# (если сильно заморочиться и автоматизировать, то можно было придумать что-нибудь с весами-влияниями через какие-нибудь библиотеки как scipy, чтобы понять от каких избавляться, от каких нет, так как медиана у нас равно 12, а среднее ~800)

# In[32]:


new_df = df.loc[df['Installs'] >= df['Installs'].mean()]


# ### Ответ:

# In[33]:


new_df.sort_values(by = ['Fraud to All', 'Fraud Installs'], ascending=False).head()


# In[34]:


(new_df['Fraud to All'].sort_values(ascending=False).head()*100).astype(str) +'%'


# In[35]:


(new_df['Fraud to All'].sort_values(ascending=True).head()*100).astype(str) +'%'


# ## 5) выведи суммарно сколько денег мы заработали, сколько заплатили за фрод и разницу между ними(итоговый заработок=прибыль-вычет)

# In[36]:


print(f"""Суммарно мы заработали {round(df['Installs'].sum() * pay_inst,2)}$
За фрод мы заплатили {-round(df['Fraud Installs'].sum() * pay_fraud, 2)}$
А итоговый наш заработок = {round(df['Installs'].sum() * pay_inst + df['Fraud Installs'].sum() * pay_fraud, 2)}$""")


# ## 6) выведи Топ-5 источников с самым высоким содержанием фрода, сколько суммарно мы заплатили за этот фрод и какой процент от всего фрода составляют эти 5 источников

# In[37]:


new_df_top_fraud = new_df.sort_values(by = ['Fraud Installs'], ascending=False).head()
new_df_top_fraud


# In[38]:


print(f"""Суммарно мы заплатили за этот фрод {-round(new_df_top_fraud['Fraud Installs'].sum() * pay_fraud, 2)}$
И он составляет {round(new_df_top_fraud['Fraud Installs'].sum() / df['Fraud Installs'].sum(), 2) * 100}% от всего фрода""")


# In[ ]:




