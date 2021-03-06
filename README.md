# cart
License plate recognition

# 标题表示 #
用井号#来标识，井号与标题之间需要加括号,共有6个等级
# One #
## Two ##
### Three ###
#### Four ####
##### Five #####
###### Six ######

# 换行 #
换行时加\<br>就可以
<br>这样子<br>就实现了换行

但是好像

回车也行


与上一行文本有一行以上的空行就可以起到换行作用


# 强调 #
<br>\*强调*   *斜体*
<br>\*\*加重强调**  **粗体**
<br>\*\*\*特别强调***  ***粗斜体***
   
<br>\_强调_    _斜体_
<br>\_\_加重强调__   __粗体__
<br>\_\_\_特别强调___  ___粗斜体___

# 代码 #
\`\`\`
    <br>代码部分
<br>\`\`\`
<br>是键盘上Tab键上方那个键
<br>在首行的\`后面加语言名称，可以让代码带颜色，美观一点

<br>比如
<br>
```python
if __name__ == '__main__':
    print_hi('PyCharm')
```

# 圆点符 #
用\*来表示，但是还是要注意空格

* 第一

* 第二

* 第三

# 文字部分的高亮 #
利用一对点\`将所需要高亮的部分框起来

Thank `You` . Please `Call` Me `Coder`

用\>引导条目有缩进并且高亮的效果

>宇宙 
>>太阳系
>>>地月系

>>>>地球 

# 链接 #
给需要加超链接的词条，用\[\]框住，后方在\(\)中加入链接，图片则需要在第一个\[前加一个！号

文字超链接:[百度](https://www.baidu.com)

图片超链接：![这个括号里写的在图片加载时显示](https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1604120293210&di=d5de2e2bd3e3891eac387718733e7152&imgtype=0&src=http%3A%2F%2Fb-ssl.duitang.com%2Fuploads%2Fitem%2F201704%2F29%2F20170429011256_f8CUr.jpeg)

直接放一个图片的超链接也可以直接显示（不是网址）
<a href="https://sm.ms/image/kGWSI7wPOBzUjdx" target="_blank"><img src="https://i.loli.net/2020/10/31/kGWSI7wPOBzUjdx.png" ></a>

# 表 #
|列名1|列名2|
|:---|:---|
|列1的内容1|列2的内容1|
|列1的内容2|列2的内容2|

<a href="https://sm.ms/image/wePquzSfakbYBcv" target="_blank"><img src="https://i.loli.net/2020/10/31/wePquzSfakbYBcv.png" ></a>

可以调整图片的大小，居中
<div align=center><img width="150" height="150" src="https://github.com/HeTingwei/ReadmeLearn/blob/master/avatar1.jpg"/></div>

<img src="https://github.com/HeTingwei/ReadmeLearn/blob/master/avatar1.jpg" width="150" height="150" alt="图片加载失败时，显示这段字"/>


# Sigflow: Streamline Analysis Workflows for Mutational Signatures 的readme #
## 标签
标签图片是来自于一个https://shields.io 网站，在其中label和message中填写信息，选择颜色，最后点击Make Badge即可得到图片地址<br>比如：

![](https://img.shields.io/badge/Recognition-test-green)

## 目录
>目录的编辑语言
<a href="https://sm.ms/image/fXbqHgdtZw7r9Az" target="_blank"><img src="https://i.loli.net/2020/10/31/fXbqHgdtZw7r9Az.png" ></a>

可以[自动生成](https://github.com/ekalinin/github-markdown-toc)，[教程](https://blog.csdn.net/qq_20009015/article/details/84728963)

安装好目录文件和readme文件，一键生成目录后再复制粘贴进readme中

mac:

$ curl https://raw.githubusercontent.com/ekalinin/github-markdown-toc/master/gh-md-toc -o gh-md-toc

$ chmod a+x gh-md-toc
 
用法./gh-md-toc 文件名.md
 
比如说直接 

./gh-md-toc /Users/mac/Desktop/README.

<a href="https://sm.ms/image/YmLt79syFgclEq6" target="_blank"><img src="https://i.loli.net/2020/10/31/YmLt79syFgclEq6.png" ></a>

Linux和os系统方便一点，Windows可以参考[这个网址](https://www.jianshu.com/p/302abe331dcb)

>`以下`是直接复制粘贴后的结果

Table of Contents
=================

   * [cart](#cart)
   * [标题表示](#标题表示)
   * [One](#one)
      * [Two](#two)
         * [Three](#three)
            * [Four](#four)
               * [Five](#five)
                  * [Six](#six)
   * [换行](#换行)
   * [强调](#强调)
   * [代码](#代码)
   * [圆点符](#圆点符)
   * [文字部分的高亮](#文字部分的高亮)
   * [链接](#链接)
   * [表](#表)
   * [Sigflow: Streamline Analysis Workflows for Mutational Signatures 的readme](#sigflow-streamline-analysis-workflows-for-mutational-signatures-的readme)
      * [标签](#标签)
      * [目录](#目录)
   * [遇到的一个问题](#遇到的一个问题)


>`以下`是在前后加入\<details>和\</details>，\<summary>和\</summary>删除"=="的结果

deatils会让内容变成下拉展开，不加summary的话，tag是“详细信息，加了summary，tag为summary中间的部分

<a href="https://sm.ms/image/pMFto3ROdkc2NaW" target="_blank"><img src="https://i.loli.net/2020/10/31/pMFto3ROdkc2NaW.png" ></a>

<details>
<summary>Table of Contents</summary>

   * [cart](#cart)
   * [标题表示](#标题表示)
   * [One](#one)
      * [Two](#two)
         * [Three](#three)
            * [Four](#four)
               * [Five](#five)
                  * [Six](#six)
   * [换行](#换行)
   * [强调](#强调)
   * [代码](#代码)
   * [圆点符](#圆点符)
   * [文字部分的高亮](#文字部分的高亮)
   * [链接](#链接)
   * [表](#表)
   * [Sigflow: Streamline Analysis Workflows for Mutational Signatures 的readme](#sigflow-streamline-analysis-workflows-for-mutational-signatures-的readme)
      * [标签](#标签)
      * [目录](#目录)
   * [遇到的一个问题](#遇到的一个问题)

</details>

# 遇到的一个问题
有时图片无法加载，查到是DNS 污染，需要在host文件中添加一个ip地址，具体可以看这个

https://blog.csdn.net/qq_41709370/article/details/106282229

https://zhuanlan.zhihu.com/p/139219691

<a href="https://sm.ms/image/rPvnM5dINxKqfcB" target="_blank"><img src="https://i.loli.net/2020/10/31/rPvnM5dINxKqfcB.png" ></a>
