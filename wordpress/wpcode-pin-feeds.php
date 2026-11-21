<?php
/**
 * Character Name Hub – Pinterest pin feeds
 *
 * Serves https://characternamehub.com/pin-feeds/<slug>.xml from the GitHub repo
 * razzaqf299-lgtm/characternamehub-pins (feeds/<slug>.xml), so the RSS feeds live on
 * your claimed domain and Pinterest can auto-publish them.
 *
 * WPCode: add as a "PHP Snippet", Insert Method "Auto Insert", Location "Run Everywhere", then Activate.
 */
add_action( 'init', function () {
	$path = trim( (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH ), '/' );
	if ( ! preg_match( '#^pin-feeds/([a-z0-9-]+)\.xml$#', $path, $m ) ) {
		return;
	}
	$slug = $m[1];
	$key  = 'cnh_pin_feed_' . $slug;
	$xml  = get_transient( $key );

	if ( false === $xml ) {
		$res = wp_remote_get(
			'https://raw.githubusercontent.com/razzaqf299-lgtm/characternamehub-pins/main/feeds/' . $slug . '.xml',
			array( 'timeout' => 15 )
		);
		if ( is_wp_error( $res ) || 200 !== (int) wp_remote_retrieve_response_code( $res ) ) {
			status_header( 404 );
			nocache_headers();
			exit;
		}
		$xml = wp_remote_retrieve_body( $res );
		set_transient( $key, $xml, 15 * MINUTE_IN_SECONDS );
	}

	status_header( 200 );
	header( 'Content-Type: application/rss+xml; charset=UTF-8' );
	header( 'Cache-Control: no-cache, max-age=0' );
	header( 'X-LiteSpeed-Cache-Control: no-cache' );
	header( 'X-Robots-Tag: noindex' );
	echo $xml; // phpcs:ignore WordPress.Security.EscapeOutput -- XML feed body.
	exit;
}, 0 );
