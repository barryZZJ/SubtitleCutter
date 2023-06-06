# SubtitleCutter
根据clt裁剪ass的时间

## 使用说明

首先在[Releases](./releases/latest)下载`SubtitleCutter.exe`和`SubtitleCutter.bat`。

> bat和exe需要在同一目录下，如果需要放在别的地方可以给bat创捷快捷方式，也支持拖放。

- 简单使用：

1. 设置全局偏移毫秒数：修改`SubtitleCutter.bat`里的`--offset`参数

   > 默认为0，可正可负，一般与File Indexer导出的音频的偏移量相同。

2. 把`ass文件`和`clt文件`同时拖放到`SubtitleCutter.bat`上即可，输出文件为`<ass文件名>_cut.ass`

- 高级使用：

  `SubtitleCutter.exe <ass路径> <clt路径>`

  可选参数：

  `--out, -o OUTPATH` 指定输出文件路径，默认为`<ass文件名>_cut.ass`

  `--offset OFFSETMS` 全局偏移毫秒数，默认为0，可正可负，一般与File Indexer导出的音频的偏移量相同。

## 代码执行逻辑

代码会先对对白进行时间平移，然后再根据clt进行裁剪，开始和结束时间都超出范围的会被丢弃，二者之一超出范围的会被clamp，开始时间与结束时间相同的会被删除。
