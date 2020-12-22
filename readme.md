### MC, HMM and LSTM for generation of music

#### Markov Chain in Music Generation

假设一首乐曲可以由一系列的随机变量(i.e.一个随机向量)表示$\boldsymbol X=(X_1,...,X_n)^T,X_i\in\mathcal N=\{1,...,m\}$, 马尔科夫链(Markov Chain)[ref...]生成音乐的基本假设是, 这些随机变量遵循马尔可夫性质,  即
$$
\forall i=1...n,P(X_{i+1}|X_{i},...,X_1)=P(X_{i+1}|X_{i})
$$
并且, 假设这些随机变量的边缘分布同分布
$$
\forall x,i,j,P_{X_i}(x)=P_{X_j}(x)
$$
 那么我们可以根据观察到的数据得到平稳分布的估计
$$
\boldsymbol \pi\approx (\hat p_i)_{i=1...m}^T
$$
其中$\hat p_i$是对观测数据中音符i出现的频率, 以及对转移矩阵的估计
$$
\bold T=(T_{ij})\approx\hat q_{ij}/\hat p_{i}
$$
其中$\hat q_{ij}$是音乐序列中$X_k=i,X_{k+1}=j$出现的次数. 由此, 我们可以通过平稳分布和概率转移矩阵得到序列联合分布
$$
\begin{aligned}
P(\bold X)&=P(X_1=x_1)\prod_i P(X_{i+1}=x_{i+1}|X_i=x_i)\\
&=\boldsymbol \pi_{x_1} \prod_i T_{x_i,x_{i+1}} 
\end{aligned}
$$
若想要从其中采样出一个序列, 我们可以简单地的通过贪心法来取到一个合理的序列
$$
x_{i+1}^*=\operatorname{argmax}_{x}P_{X_{i+1}|X_i}(x|x_i)
$$
也可以采用简单的采样法来取得一个序列
$$
x_{i+1}^*\sim P_{X_{i+1}|X_i}(x|x_i)
$$
我们也可以最大化这些序列的对数似然
$$
\bold X=\arg\max_{\bold X} \operatorname{LLD}(\bold X)=\arg\min_{\bold X}  \log \boldsymbol \pi_{x_1} \sum_i T_{x_i,x_{i+1}}
$$
可以通过动态规划算法求出确定性的最优解, 其状态转移方程如下
$$
F(i,j)=\max_k F(i-1,k)-\log T_{k,j}
$$
这里$F(i,j)$代表取一个长为i的序列, 且结尾音符为j时最大的对数似然, 时间复杂度是$O(n m^2=T|\mathcal N|^2)$. 除了以上列举的一些简单方法, 其实还有一种有趣的采样方法, 就是Gibbs采样, 通过将Markov链绕成一个环, 我们可以得到对称的条件概率模式
$$
P(X_{i}|\bold X-\{X_i\})=P(X_{i}|X_{i-1\operatorname{mod}n})
$$
于是我们可以通过Gibbs采样来得到一个概率较高的样本. 概括的来讲,Gibbs采样每次固定除了一个分量之外的其它分量, 并根据条件概率分布对没有固定的分量进行采样, 然后轮流对每一个分量进行如此操作, 可以证明, 如此进行足够多的轮数之后, 序列收敛于联合分布(即整个Markov Chain)的一个最概然序列. 值得一提的是Gibbs采样也广泛用于大量其它种类的概率分布的采样, 衍生出了MCMC等概率模型中的重要方法.

| Gibbs Sampling                                               |
| ------------------------------------------------------------ |
| 1. $\forall i,x_i\sim RandomChoice(\mathcal H )$             |
| 2. For i = 1...k, $x_{i\operatorname{mod}m}=RandomSample(P(X_{i}|\bold X-\{X_i\})=P(X_{i}|X_{i-1\operatorname{mod}n}))$ |

#### HMM: Hidden States in Music

可以想见, 在乐曲并不完全遵循Markov性质, 一首乐曲的某个音符很难只由其上一个音符决定, 而往往由上一段乐曲, 以及整段乐曲及其部分的语义决定. 隐式马尔可夫模型(HMM, Hidden Markov Model)指出, 一段观察序列$\boldsymbol O=(O_1,...,O_n)^T,O_i\in\mathcal N=\{1,...,m\}$可能由隐含状态$$\boldsymbol X=(X_1,...,X_n)^T,X_i\in\mathcal H=\{1,...,h\}$$所决定, 其中隐含状态又是符合Markov性质转移的, 某种意义上代表着序列某时刻的语义信息(比如此时应该时舒缓还是激烈, 欢快或是忧伤), 同样具有转移矩阵, 以及(若可能)的估计
$$
\bold T=(T_{ij})\approx\hat q_{ij}/\hat p_{i}
$$
以及输出矩阵, 决定了从隐含状态到观察状态的转移概率, 通过对隐含状态和观察状态的共同观察, 可以估计得到
$$
\bold E=(E_{ij})\approx\hat r_{ij}/\hat p_{i}
$$
其中$\hat r_{ij}$是音乐序列中$X_k=i,O_k=j$出现的次数. 不过一般来说, 我们难以得知隐含状态的序列, 而往往只知道观察状态的序列, 这时候我们就需要利用Baum-Welch算法来估计一个转移矩阵(以及输出矩阵), 其对应了最大的观察序列的后验对数似然. Baum-Welch算法是EM算法的一个应用, 这里我们将不介绍他的推导[ref...], 而是直接给出更新公式.

...Baum-Welch...

得到最优的转移矩阵和输出矩阵后, 也可以和显式马尔科夫模型一样通过贪心, 直接采样和动态规划的方法求出一些较好的序列. 

#### LSTM: Recurrent Networks in Music Generation

HMM部分解决了乐曲隐含语义的问题, 将其编码在了模型的隐含状态中, 但是没有解决乐曲的另一个特性: 一个音符往往不只是和前一个时刻的状态有关, 而是和之前数个甚至是整段乐曲有关. 递归神经网络利用时序传播特性完美编码了这种特性, 其中最实用和有趣的模型就是长短时记忆网络(LSTM, Long Short Term Memory Network)[ref...].

