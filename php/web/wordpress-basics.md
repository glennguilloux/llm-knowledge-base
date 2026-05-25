---
id: "php-web-wordpress-basics"
title: "WordPress Development: Plugins, Hooks, Shortcodes, Custom Post Types"
language: "php"
category: "web"
tags: ["php", "wordpress", "plugins", "hooks", "shortcodes", "cpt"]
version: "6.x+"
retrieval_hint: "php wordpress plugin development hooks actions filters shortcodes custom post types WP_Query"
last_verified: "2026-05-24"
confidence: "high"
---

# WordPress Development: Plugins, Hooks, Shortcodes, Custom Post Types

## When to Use
- Extending WordPress with custom functionality
- Creating WordPress plugin packages
- Adding custom post types and taxonomies
- Building shortcodes for content embedding
- Writing secure, maintainable WordPress code

## Standard Pattern

```php
<?php
/**
 * Plugin Name: Project Manager
 * Plugin URI:  https://example.com/project-manager
 * Description: Manages projects and tasks within WordPress
 * Version:     1.0.0
 * Author:      Your Name
 * License:     GPL v2 or later
 * Text Domain: project-manager
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// --- Constants ---
define('PM_VERSION', '1.0.0');
define('PM_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('PM_PLUGIN_URL', plugin_dir_url(__FILE__));

// --- Activation Hook ---
register_activation_hook(__FILE__, 'pm_activate');
function pm_activate(): void {
    pm_register_post_types();
    flush_rewrite_rules();
}

// Deactivation
register_deactivation_hook(__FILE__, 'pm_deactivate');
function pm_deactivate(): void {
    flush_rewrite_rules();
}

// --- Custom Post Type ---
add_action('init', 'pm_register_post_types');
function pm_register_post_types(): void {
    register_post_type('pm_project', [
        'labels' => [
            'name'          => __('Projects', 'project-manager'),
            'singular_name' => __('Project', 'project-manager'),
            'add_new_item'  => __('Add New Project', 'project-manager'),
            'edit_item'     => __('Edit Project', 'project-manager'),
        ],
        'public'        => true,
        'show_in_rest'  => true,
        'menu_icon'     => 'dashicons-portfolio',
        'supports'      => ['title', 'editor', 'thumbnail', 'custom-fields'],
        'rewrite'       => ['slug' => 'projects'],
        'has_archive'   => true,
    ]);

    // Custom taxonomy
    register_taxonomy('pm_status', 'pm_project', [
        'labels' => [
            'name'          => __('Statuses', 'project-manager'),
            'singular_name' => __('Status', 'project-manager'),
        ],
        'public'        => true,
        'show_in_rest'  => true,
        'hierarchical'  => true,
        'rewrite'       => ['slug' => 'status'],
    ]);
}

// --- Actions and Filters ---
// Enqueue scripts
add_action('wp_enqueue_scripts', 'pm_enqueue_scripts');
function pm_enqueue_scripts(): void {
    if (is_singular('pm_project')) {
        wp_enqueue_style('pm-style', PM_PLUGIN_URL . 'assets/style.css', [], PM_VERSION);
        wp_enqueue_script('pm-script', PM_PLUGIN_URL . 'assets/script.js', ['jquery'], PM_VERSION, true);
        wp_localize_script('pm-script', 'pm_ajax', [
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce'    => wp_create_nonce('pm_nonce'),
        ]);
    }
}

// Modify content
add_filter('the_content', 'pm_append_project_meta');
function pm_append_project_meta(string $content): string {
    if (!is_singular('pm_project')) {
        return $content;
    }

    $deadline = get_post_meta(get_the_ID(), '_pm_deadline', true);
    if ($deadline) {
        $content .= '<p class="pm-deadline">';
        $content .= esc_html__('Deadline: ', 'project-manager') . esc_html($deadline);
        $content .= '</p>';
    }

    return $content;
}

// --- Shortcode ---
add_shortcode('pm_project_list', 'pm_project_list_shortcode');
function pm_project_list_shortcode(array $atts): string {
    $atts = shortcode_atts([
        'status' => '',
        'limit'  => 5,
    ], $atts, 'pm_project_list');

    $args = [
        'post_type'      => 'pm_project',
        'posts_per_page' => intval($atts['limit']),
        'meta_key'       => '_pm_deadline',
        'orderby'        => 'meta_value',
        'order'          => 'ASC',
    ];

    if (!empty($atts['status'])) {
        $args['tax_query'] = [
            [
                'taxonomy' => 'pm_status',
                'field'    => 'slug',
                'terms'    => sanitize_title($atts['status']),
            ],
        ];
    }

    $query = new WP_Query($args);
    ob_start();

    if ($query->have_posts()) {
        echo '<ul class="pm-project-list">';
        while ($query->have_posts()) {
            $query->the_post();
            printf(
                '<li><a href="%s">%s</a></li>',
                esc_url(get_permalink()),
                esc_html(get_the_title())
            );
        }
        echo '</ul>';
        wp_reset_postdata();
    } else {
        echo '<p>' . esc_html__('No projects found.', 'project-manager') . '</p>';
    }

    return ob_get_clean();
}

// --- AJAX Handler ---
add_action('wp_ajax_pm_update_status', 'pm_ajax_update_status');
add_action('wp_ajax_nopriv_pm_update_status', 'pm_ajax_update_status');
function pm_ajax_update_status(): void {
    check_ajax_referer('pm_nonce');

    if (!isset($_POST['post_id'], $_POST['status'])) {
        wp_send_json_error('Missing parameters');
    }

    $post_id = intval($_POST['post_id']);
    $status = sanitize_text_field($_POST['status']);

    if (!current_user_can('edit_post', $post_id)) {
        wp_send_json_error('Insufficient permissions');
    }

    wp_set_object_terms($post_id, $status, 'pm_status');
    wp_send_json_success(['status' => $status]);
}

// --- Options / Settings API ---
add_action('admin_menu', 'pm_add_admin_menu');
function pm_add_admin_menu(): void {
    add_options_page(
        __('Project Manager Settings', 'project-manager'),
        __('Projects', 'project-manager'),
        'manage_options',
        'project-manager',
        'pm_settings_page'
    );
}

function pm_settings_page(): void {
    if (isset($_POST['pm_save'])) {
        check_admin_referer('pm_settings');
        update_option('pm_default_status', sanitize_text_field($_POST['pm_default_status']));
        echo '<div class="notice notice-success"><p>' . esc_html__('Settings saved.', 'project-manager') . '</p></div>';
    }
    $default = get_option('pm_default_status', 'planning');
    ?>
    <div class="wrap">
        <h1><?php esc_html_e('Project Manager Settings', 'project-manager'); ?></h1>
        <form method="post">
            <?php wp_nonce_field('pm_settings'); ?>
            <table class="form-table">
                <tr>
                    <th><label for="pm_default_status"><?php esc_html_e('Default Status', 'project-manager'); ?></label></th>
                    <td><input type="text" id="pm_default_status" name="pm_default_status"
                               value="<?php echo esc_attr($default); ?>" class="regular-text"></td>
                </tr>
            </table>
            <p class="submit"><button type="submit" name="pm_save" class="button-primary">
                <?php esc_html_e('Save Changes', 'project-manager'); ?>
            </button></p>
        </form>
    </div>
    <?php
}
```

## Common Mistakes

```php
<?php

// WRONG: Direct database queries (bypass WP APIs)
global $wpdb;
$results = $wpdb->get_results("SELECT * FROM wp_posts WHERE post_type = 'project'");
// Bypasses caching, post type registration, and WP filters

// CORRECT: Use WP_Query
$query = new WP_Query(['post_type' => 'project', 'posts_per_page' => -1]);


// WRONG: Not prefixing function/class names (collision risk)
function get_projects() { /* ... */ }  // Could conflict with another plugin

// CORRECT: Prefix everything
function pm_get_projects() { /* ... */ }  // Unique prefix prevents collisions


// WRONG: Not using nonces for forms
<form method="post">
    <input type="hidden" name="action" value="delete_project">
    <input type="submit" value="Delete">
</form>
// CSRF vulnerability — anyone can submit this form!

// CORRECT: Use wp_nonce_field
<form method="post">
    <?php wp_nonce_field('delete_project_' . $project_id); ?>
    <input type="hidden" name="action" value="delete_project">
    <input type="submit" value="Delete">
</form>

// Verify: check_admin_referer('delete_project_' . $project_id);


// WRONG: Escaping output inconsistently
echo "<h2>" . $title . "</h2>";  // XSS vulnerability!
echo "<p>$description</p>";       // XSS vulnerability!

// CORRECT: Always escape
echo '<h2>' . esc_html($title) . '</h2>';
echo '<p>' . esc_html($description) . '</p>';
```

## Gotchas
- **Global `$wpdb`**: Always declare `global $wpdb;` before using it. The `$wpdb->prefix` is configurable (not always `wp_`), so always use `$wpdb->prefix` in table names.
- **`is_admin()` vs `wp_doing_ajax()`**: `is_admin()` returns true for AJAX handlers too. Use `wp_doing_ajax()` to specifically check for AJAX requests. Admin page checks should use `is_admin() && !wp_doing_ajax()`.
- **`the_content` filter ordering**: Multiple plugins modify `the_content` filter. Priority determines execution order. Use priority 10 for defaults, 20+ for late modifications.
- **Rewrite rules**: When registering custom post types or taxonomies, call `flush_rewrite_rules()` only on plugin activation/deactivation, not on every page load. Never call it on `init`.
- **Query performance**: `WP_Query` with `posts_per_page => -1` loads all matching posts into memory. Always paginate with `paged` parameter.
- **`wp_reset_postdata()`**: After a custom `WP_Query` loop, always call `wp_reset_postdata()` to restore the global `$post` variable to the original query.
- **Internationalization**: Use WordPress i18n functions (`__()`, `_e()`, `esc_html__()`) with the plugin's text domain for all user-facing strings.

## Related
- php/stdlib/basics.md
- php/security/common-vulnerabilities.md
