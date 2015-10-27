<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<?php
header("Content-Type: text/html;charset=utf-8");
?>
<head>
<meta http-equiv='Content-Type' content='text/html; charset=utf-8' />
<title>baidupan search</title>
<style type="text/css">
<!--
.STYLE1 {font-size: larger}
.STYLE2 {
	font-size: xx-large;
	font-family: Geneva, Arial, Helvetica, sans-serif;
	color: #0066CC;
}
.STYLE3 {
	color: #666666;
	font-size: 12px;
}
-->
</style>
</head>

<body>
<p>&nbsp;</p>
<p align="center">&nbsp;</p>
<p align="center">&nbsp;</p>
<p align="center">&nbsp;</p>
<form action="/search.php" method="get">
        <div align="center">
          <p class="STYLE2">BaiduPan Search</p>
          <p>
            <input name="q" type="text" size="80">
            <input type="hidden" name="start" value="1">
            <input type="submit" value="Search">
          </p>
  </div>
        <span class="STYLE1"></span>
</form>

</body>
</html>
