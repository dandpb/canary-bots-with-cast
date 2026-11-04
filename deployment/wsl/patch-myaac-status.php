<?php
// MyAAC settings return a numeric port, while the original code tests string offsets.
$path = '/var/www/html/system/status.php';
$source = file_get_contents($path);
$original = <<<'PHP'
$settingPort = setting('core.status_port');
if(isset($settingPort[0])) {
	$status_port = $settingPort;
}
elseif(!isset($status_port[0])) // try 7171 if no port specified
{
	$status_port = 7171;
}
PHP;
$replacement = <<<'PHP'
$settingPort = setting('core.status_port');
$portOptions = ['options' => ['min_range' => 1, 'max_range' => 65535]];
$configuredPort = filter_var($settingPort, FILTER_VALIDATE_INT, $portOptions);
$luaPort = filter_var($status_port, FILTER_VALIDATE_INT, $portOptions);
$status_port = $configuredPort !== false ? $configuredPort : ($luaPort !== false ? $luaPort : 7171);
PHP;
if (substr_count($source, $original) !== 1) {
    throw new RuntimeException('Unexpected MyAAC status-port implementation; review the compatibility patch.');
}
file_put_contents($path, str_replace($original, $replacement, $source));
