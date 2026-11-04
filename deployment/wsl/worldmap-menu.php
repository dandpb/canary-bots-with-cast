<?php
$db = new PDO(
    'mysql:host=' . getenv('CANARY_DB_HOST') . ';dbname=' . getenv('CANARY_DB_NAME') . ';charset=utf8mb4',
    getenv('CANARY_DB_USER'), getenv('CANARY_DB_PASSWORD'),
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
);
$db->exec("INSERT INTO myaac_menu (template, name, link, blank, color, category, ordering, enabled)
    SELECT m.template, 'World Map', 'worldmap', m.blank, m.color, m.category, m.ordering + 1, 1
    FROM myaac_menu m WHERE m.link = 'online' AND m.category = 3
    AND NOT EXISTS (SELECT 1 FROM myaac_menu existing WHERE existing.template = m.template AND existing.link = 'worldmap')");
foreach (['status_ip' => 'game', 'status_port' => '7173', 'client' => '1500'] as $key => $value) {
    $insert = $db->prepare('INSERT INTO myaac_settings (`name`, `key`, `value`) SELECT ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM myaac_settings WHERE `name` = ? AND `key` = ?)');
    $insert->execute(['core', $key, $value, 'core', $key]);
    $update = $db->prepare('UPDATE myaac_settings SET `value` = ? WHERE `name` = ? AND `key` = ?');
    $update->execute([$value, 'core', $key]);
}
echo "World map menu is ready.\n";
