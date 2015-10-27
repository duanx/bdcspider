<html>
<head>
<meta http-equiv='Content-Type' content='text/html; charset=utf-8' />
<title>BaiduPan Search</title>
<style type="text/css">
        body{color:#BFFEE3;background:#FEFEFE;padding:0 5em;margin:0}
        h2{padding:2em 1em;background:#FFFFFF}
        h3{color:#0066CC;margin:1em 0}
        h4{color:#000000;margin:1em 0}
        p{color:#000000;margin:1em 0}
</style>
</head>
<?php
/***************************************************************/
function splitkey($key,$split)
{
    $i=0;

    $retarr=array();
    $token= strtok($key, $split);

    while ($token !== false)
    {
        $retarr[$i]=$token;
        $token = strtok(" ");
        $i++;
    }
    return $retarr;
}

function show($val)
{
    return iconv("GB2312","UTF-8",$val);
}
/***************************************************************/
header("Content-Type: text/html;charset=utf-8");
@$key=$_GET['q'];
if(!$key)
    $key="null";

@$start=$_GET['start'];
define("PWD", "Duanx1234");
define("NAME", "root");
define("SERVER", "localhost:3306");
define("DB", "test");
define("QUERY", "select * from sourcedata where");
define("TOTAL", "select count(1) from sourcedata where");

define("ROWMAX",10);
define("PAGEMAX",10);

class bdatabase
{
    private $sqlfd;
    private $queryret;
    private $key;

    private $page_start;
    private $page_end;
    private $page_cur;
    private $pages;
    public $querysize;

    function open($server,$name,$pwd)
    {
        if(!$this->sqlfd = mysql_connect($server,$name,$pwd))
        {
            die('Could not connect: ' . mysql_error());
        }
        mysql_select_db(DB, $this->sqlfd);
    }

    function close()
    {
        mysql_close($this->sqlfd);
    }

    function showrecords()
    {
        while($row=$this->searchrow())
        {
            echo "<li> 
                <h4><a target=\"_blank\" href=\"" . $row['url'] . "\">" . $row['name'] . "</a></h4>  
                <p>" . show('分享时间:') . $row['sharetime'] . "</p> 
                </li>";
        }
    }

    function search($key,$page)
    {
        $i=0;
        $keys=splitkey($key," ");
        $argc=sizeof($keys);
        $argv=$keys;
        $pageindex=0;

        $this->key=$key;

        /*
         * assemble sql with count
         */
        $q=TOTAL;
        while($i<$argc){
            if($i)
                $q=$q . " and";
            $q=$q . " name like '%" . $argv[$i] . "%'";
            $i++;
        }
        if (!$result=mysql_query($q,$this->sqlfd))
            die("connect database failed\n");
        $row = mysql_fetch_array($result);
        $this->querysize= $row[0];
        if(!$this->querysize)
            return true;
        $this->pages=($this->querysize+PAGEMAX-1)/PAGEMAX;
        $this->pages=floor($this->pages);
        if($page<0 || $page>$this->pages){
            die("page:" . $page . " was out of range");
            return false;
        }

        $this->page_cur=$page;

        $ret=floor($page-(PAGEMAX/2-1));
        $this->page_start=$ret<=0?1:$ret;

        $ret=floor($page+PAGEMAX/2);
        $this->page_end=$ret>$this->pages?$this->pages:$ret;

        /*
         * assemble sql with search
         */
        $q=QUERY;
        $i=0;
        while($i<$argc){
            if($i)
                $q=$q . " and";
            $q=$q . " name like '%" . $argv[$i] . "%'";
            $i++;
        }
        $q=$q . " limit " . ($page-1)*PAGEMAX . "," . PAGEMAX;
        if ($this->queryret=mysql_query($q,$this->sqlfd)){
            return true;
        }else{
            die("Error creating database: " . mysql_error());
        }
    }
    function searchrow()
    {
        if(!$this->queryret)
            return null;
        else
            return mysql_fetch_array($this->queryret);
    }
    function paging()
    {
        echo "<a href=\"/search.php?q=" . $this->key . "&start=" . ($this->page_cur>1?($this->page_cur-1):$this->page_cur) . "\">" . show("上一页") . "</a>&nbsp;";
        $i=$this->page_start;
        while($i<=$this->page_end){
            if($i==$this->page_cur)
                echo "<a href=\"/search.php?q=" . $this->key . "&start=" . $i . "\"><strong>" . $i . "</strong></a>&nbsp;";
            else
                echo "<a href=\"/search.php?q=" . $this->key . "&start=" . $i . "\">" . $i . "</a>&nbsp;";
            $i++;
        }
        echo "<a href=\"/search.php?q=" . $this->key . "&start=" . ($this->page_cur<$this->pages?($this->page_cur+1):$this->page_cur) . "\">" . show("下一页") . "</a>&nbsp;";
    }
}
?>
<body>
<div align="center">
<form action="/search.php" method="get">
<h3>BaiDuPan Search</h3> 
<input name="q" type="text" size="50" value="<?php echo $key;?>">
  <input type="hidden" name="start" value="1">
  <input type="submit" value="Search">
</form>
</div>
<div>
<ul>
<?php
$dbs=new bdatabase();
$dbs->open(SERVER,NAME,PWD);
$queryret=$dbs->search($key,$start);

$dbs->showrecords();
$dbs->close();
?>
</ul>
</div>
<p>
<?php
$total=0;
echo $dbs->querysize . show('条结果');
?>
</p>
<div align="center">
<?php
$dbs->paging();
?>
</div>
<p>
</body>
</html>

