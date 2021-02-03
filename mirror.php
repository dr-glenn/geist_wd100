<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="60">
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
    }
    fclose($fp);
    return $LastLine;
}

// shell script that runs python data logger will also exrtact
// last line from log file and put it in it's own file.
// Use this function instead of read_last_log_all, it's more efficient.
function read_last_dat($sensor) {
    $fp = fopen("/home/pi/Projects/geist_wd100/".$sensor."_newest.dat", "r");
    $LastLine = fgets($fp, 4096);
    fclose($fp);
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
    background-color: lightgrey;
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
.grey_steady {
    background-color: grey;
}
.white_steady {
    background-color: white;
}
</style>
</head>
<body>
<h1>OOS Environment</h1>
<?php
$mirror_stat = 'green';
$status_class = '';
// read files 'geist_newest.dat' or 'pi_newest.dat' for environment data

// instrument log files written by Python have device names, which are hard to comprehend.
// Get an alias until we improve the Python code.
function get_friendly_instr_name($instr) {
    $nice_name['ds18b20-0']   = 'mirror';
    $nice_name['dht22']       = 'mirror cell';
    $nice_name['dew_cell']    = 'mirror cell';
    $nice_name['dew_mirror']  = 'mirror';
    $nice_name['relay']       = 'heater';
    $nice_name['Geist WD100'] = 'Geist chassis';
    $nice_name['GTHD']        = 'Geist external';

    if (array_key_exists($instr, $nice_name)) {
        return $nice_name[$instr];
    }
    else {
        return $instr;
    }
}

function gen_table_rows($fname) {
    global $mirror_stat;
    $fp = fopen($fname, "r");
    $tab_rows = "";
    while($line = fgets($fp,2048)) {
        $flds = explode(',', $line);
        $datetime = $flds[0];
        $instr = $flds[1];
        $nice_name = get_friendly_instr_name($instr);
        $tab_rows .= "<tr><td>".$datetime."</td><td>".$nice_name."</td><td>";
        $ifld = 2;
        while ($ifld <= count($flds)-1) {
            // remove EOL
            $val = rtrim($flds[$ifld]);
	    // extract the status color
            if (strpos($val,'status=') === 0) {
                $ipos = strpos($val,'=');
                $mirror_stat = substr($val,$ipos+1);
            }
            $tab_rows .= $val;
            if ($ifld < count($flds)-1) {
                $tab_rows .= ", ";
            }
            $ifld++;
        }
        $tab_rows .= "</td></tr>";
    }
    fclose($fp);
    return $tab_rows;
}

$LastLine = read_last_dat('pi');
sscanf($LastLine, "%[^ ] %[^,]%[^\n]",$date,$time,$leftover);
sscanf($time, "%d:%d:%d", $hour, $minute, $second);

$trows = gen_table_rows('/home/pi/Projects/geist_wd100/geist_newest.dat');
$trows .= gen_table_rows('/home/pi/Projects/geist_wd100/pi_newest.dat');

// Use $mirror_stat to set background color
if (strcmp($mirror_stat,"red") == 0) {
    $status_class = "red_flasher";
}
else if (strcmp($mirror_stat,"yellow") == 0) {
    $status_class = "yellow_steady";
}
else if (strcmp($mirror_stat,"green") == 0) {
    $status_class = "green_steady";
}
else {
    $status_class = 'grey_steady';
}
//printf("<p>mirror_stat = ". $mirror_stat . ", status_class=".$status_class."</p>");

// demonstrate changing background color depending on the minute value
/*
if ($minute % 15 == 0) {
    $mirror_stat = "red";
    $status_class = "red_flasher";
}
else if ($minute % 10 == 0) {
    $mirror_stat = "yellow";
    $status_class = "yellow_steady";
}
else if ($minute % 5 == 0) {
    $mirror_stat = "green";
    $status_class = "green_steady";
}
*/
// insert javascript to store date-time values
printf("<script>\$date=%s;\$time=%s;",$date,$time);
printf("\$hour=%d;\$minute=%d</script>",$hour, $minute);
?>
<!-- big colored DIV to display status of mirror environment -->
<div id="status" style="height:120px; font-size:48px; padding: 60px 0;" class="<?php echo $status_class;?>">STATUS: <?php echo $mirror_stat; ?>
<!-- display table of Geist WD100 values -->
<div style="position:relative; margin-top:120px; padding-top:1em;">
<table>
<tr><th>Time</th><th>Location</th><th>Values</th></tr>
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
            if (strpos($flds[$ifld],'status=') === 0) {
                // extract the status color
                $ipos = strpos($flds[$ifld],'=');
                $env_stat = substr($flds[$ifld],$ipos+1);
            }
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

/*
write_table('/home/pi/Projects/geist_wd100/geist_newest.dat');
write_table('/home/pi/Projects/geist_wd100/pi_newest.dat');
*/
printf($trows);
?>
</table>
</div>
</body>
</html>
