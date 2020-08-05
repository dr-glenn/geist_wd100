<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="300">
<title>OOS Mirror Sensors</title>
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
function read_last_log_all($sensor) {
    $fp = fopen("/home/pi/Projects/geist_wd100/".$sensor."_data.log", "r");
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
function read_last_dat($sensor) {
/*
    $fp = fopen("/home/pi/Projects/geist_wd100/".$sensor."_newest.dat", "r");
    $LastLine = fgets($fp, 4096);
    fclose($fp);
    if (strlen($LastLine) == 0) {
        // the file must be bad, use the slow method
        $LastLine = read_last_log_all($sensor);
    }
*/
    $LastLine = read_last_log_all($sensor);
    return $LastLine;
}
?>

<style>
table {
    border: 5px solid black;
}
th, td {
    border: 1px solid black;
    font-size: 24px;
    padding: 10px;
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
<?php
//$LastLine = read_last_log_all('geist');
$LastLine = read_last_dat('geist');

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
// insert javascript to store date-time values
printf("<script>\$date=%s;\$time=%s;",$date,$time);
printf("\$hour=%d;\$minute=%d</script>",$hour, $minute);
?>
<!-- display table of Geist WD100 values -->
<p>
<table>
<tr><th>Time</th><th>Instrument</th><th>Values</th></tr>
<?php
function write_table($fname) {
    $fp = fopen($fname, "r");
    while($line = fgets($fp,2048)) {
        $flds = explode(',', $line);
        $datetime = $flds[0];
        $instr = $flds[1];
        printf("<tr><td>".$datetime."</td><td>".$instr."</td><td>");
        $ifld = 2;
        while ($ifld <= count($flds)-1) {
            printf($flds[$ifld]);
            if ($ifld < count($flds)-1) {
                printf(", ");
            }
            $ifld++;
        }
        printf("</td></tr>");
    }
    fclose($fp);
}

write_table('/home/pi/Projects/geist_wd100/geist_newest.dat');
write_table('/home/pi/Projects/geist_wd100/pi_newest.dat');
?>
</table>
</p>
<!-- big colored DIV to display status of mirror environment -->
<div id="status" style="height:140px; font-size:48px; padding: 60px 0;" class="<?php echo $status_class;?>">STATUS: <?php echo $mirror_stat; ?></div>
</body>
</html>