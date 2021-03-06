<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="300">
<title>OOS Geist Watchdog</title>
<?php
function get_status_color($tmirror, $dewpoint) {
    $tdiff = $tmirror - $dewpoint;
    if ($tdiff >= 10.0) $color = 'green';
    else if ($tdiff >= 5.0) $color = 'yellow';
    else $color = 'red';
    return $color;
}

// open latest log file and retrieve last line by stepping backwards.
// Note: not terribly efficient - what if log file is long?
function read_last_log_all() {
    $fp = fopen("/home/pi/Projects/geist_wd100/geist_data.log", "r");
    fseek($fp, -1, SEEK_END); // position on last char in file
    $pos = ftell($fp);
    $LastLine = "";
    // file might have trailing newlines, so skip those
    while(($C = fgetc($fp)) === "\n") {
        $pos--;
        fseek($fp, $pos, SEEK_SET);
    }
    fseek($fp, $pos, SEEK_SET);	// position back to valid char
    
    // TODO: it might fail if log only has one line
    // Loop backward until "\n" is found.
    while((($C = fgetc($fp)) != "\n") && ($pos > 0)) {
        $LastLine = $C.$LastLine;
        $pos--;
        fseek($fp, $pos);
        //printf("1: ftell=%u, C=%s<br>",ftell($fp),$C);
    }
    fclose($fp);
    //printf("pos end=%u<br>",$pos);
    //printf("str len=%u<br>",strlen($LastLine));
    //printf("Most recent: %s",$LastLine);
    return $LastLine;
}

// shell script that runs python data logger will also exrtact
// last line from log file and put it in it's own file.
// Use this function instead of read_last_log_all, it's more efficient.
function read_last_dat() {
/*
    $fp = fopen("/home/pi/Projects/geist_wd100/geist_newest.dat", "r");
    $LastLine = fgets($fp, 4096);
    fclose($fp);
    if (strlen($LastLine) == 0) {
        // the file must be bad, use the slow method
        $LastLine = read_last_log_all();
    }
*/
    $LastLine = read_last_log_all();
    return $LastLine;
}
?>

<style>
table, th, td {
    border: 1px solid black;
    font-size: 24px;
}
body {
    background-color: grey;
}
@keyframes flash_red {
    0% {background-color: red;}
    70% {background-color: red; }
    100% {background-color: blue;}
}

.red_flasher {
    background-color: grey;
    animation-name: flash_red; animation-duration: 2s; animation-iteration-count: infinite;
}

.green_steady {
    background-color: green;
}

.yellow_steady {
    background-color: yellow;
}
</style>
</head>
<body>
<h1>OOS Environment</h1>
<p>
<?php
//$LastLine = read_last_log_all();
$LastLine = read_last_dat();

sscanf($LastLine, "INFO : %[^ ] %[^,]%[^\n]",$date,$time,$leftover);
sscanf($time, "%d:%d:%d", $hour, $minute, $second);
// demonstrate changing background color depending on the minute value
if ($minute % 15 == 0) {
    $mirror_stat = "red";
    $status_class = "red_flasher";
    //printf("<style>body {background-color: red;}</style>");
}
else if ($minute % 10 == 0) {
    $mirror_stat = "yellow";
    $status_class = "yellow_steady";
    //printf("<style>body {background-color: yellow;}</style>");
}
else if ($minute % 5 == 0) {
    $mirror_stat = "green";
    $status_class = "green_steady";
    printf("<style>body {background-color: grey;}</style>");
    //printf("<style>body {background-color: grey; animation-name: flash_red; animation-duration: 2s; animation-iteration-count: infinite;}</style>");
}
// insert javascript
printf("<script>\$date=%s;\$time=%s;",$date,$time);
printf("\$hour=%d;\$minute=%d</script>",$hour, $minute);
printf("<br><table><tr><td colspan='2' style='text-align:center;'>Date=%s, Time=%s</td></tr>", $date, $time);
//printf("<br><table><tr><td colspan=2 >Date=%s, Time=%s</td></tr>", $date, $time);
printf("<tr><th>Instrument</th><th>Enviroment</th></tr>");
// don't know how much string remains, but if small amount, then not valid
$cnt = 0;
while (strlen($leftover) > 8 && $cnt < 10) {
    $more = "";
    $ret = sscanf($leftover, ",I:%[^,],V:%[^,],%f,V:%[^,],%f,V:%[^,],%f%[^\n]",$instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3,$more);
    //printf("<br>ret=%d",$ret);
    //printf("<br>more=%s",$more);
    $leftover = $more;
    //printf("<br>leftover=%s",$leftover);
    //printf("<br>instr=%s, %s=%.1f, %s=%.1f, %s=%.1f", $instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3);
    printf("<tr><td>%s</td><td>%s=%.1f, %s=%.1f, %s=%.1f</td></tr>", $instr1,$vtype1,$v1,$vtype2,$v2,$vtype3,$v3);
    $cnt++;
    if ($ret == -1) break;
}
printf("</table>");
    //printf("<style>body {background-color: grey; animation-name: flash_red; animation-duration: 2s; animation-iteration-count: infinite;}</style>");
?>
</p>
<div id="status" style="height:140px; font-size:48px; padding: 60px 0;" class="<?php echo $status_class;?>">STATUS: <?php echo $mirror_stat; ?></div>
</body>
</html>
