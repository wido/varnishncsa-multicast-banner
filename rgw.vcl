backend cloudstack {
    .host = "127.0.0.1";
    .port = "8080";
}

backend rgw {
    .host = "127.0.0.1";
    .port = "80";
    .first_byte_timeout = 5s;
    .connect_timeout = 1s;
    .probe = {
        .timeout = 250 ms;
        .interval = 10s;
        .window = 10;
        .threshold = 8;
        .request =
            "GET / HTTP/1.1"
            "Host: localhost"
            "User-Agent: Varnish-health-check"
            "Connection: close";
    }
}

sub vcl_recv {
    if (req.restarts == 0) {
        set req.http.X-Forwarded-For = client.ip;
    }

    set req.http.host = regsub(req.http.host, ":80$", "");

    if (req.http.host == "cloudstack.ceph.widodh.nl") {
        set req.backend = cloudstack;
        set req.hash_always_miss = true;
        return(pass);
    } else {
        set req.backend = rgw;
    }

    /*
     * From here we assume the RADOS Gateway
     */

    /* Should the backends not respond, keep serving what's in the cache */
    if (!req.backend.healthy) {
        set req.grace = 60m;
    } else {
        set req.grace = 15s;
    }

    if (req.http.Accept-Encoding) {
        if (req.http.Accept-Encoding ~ "gzip") {
            set req.http.Accept-Encoding = "gzip";
        } else if (req.http.Accept-Encoding ~ "deflate") {
            set req.http.Accept-Encoding = "deflate";
        } else if (req.http.Accept-Encoding ~ "identity") {
            set req.http.Accept-Encoding = "identity";
        } else {
            unset req.http.Accept-Encoding;
        }
    }

    /* Request various incoming headers we don't need */
    unset req.http.Cookie;
    unset req.http.DNT;
    unset req.http.User-Agent;
    unset req.http.Referer;

    /* We only deal with these types of HTTP request, we can block the rest */
    if (req.request != "GET" &&
       req.request != "HEAD" &&
       req.request != "PUT" &&
       req.request != "POST" &&
       req.request != "TRACE" &&
       req.request != "OPTIONS" &&
       req.request != "DELETE") {
        error 400 "Bad Request";
    }

    /* When this header is sent we can't cache anything */
    if (req.http.Authorization) {
        return (pass);
    }

    /* We can only cache GET and HEAD request */
    if (req.request != "GET" && req.request != "HEAD") {
        return (pass);
    }

    return (lookup);
}

sub vcl_pass {
     return (pass);
}

sub vcl_hash {
    hash_data(req.url);
    hash_data(req.http.host);
    return (hash);
}

sub vcl_hit {
     return (deliver);
}

sub vcl_miss {
     return (fetch);
}

sub vcl_fetch {
    set beresp.ttl = 6h;

    return (deliver);
}

sub vcl_deliver {
    unset resp.http.X-Powered-By;
    unset resp.http.Server;
    unset resp.http.Via;
    unset resp.http.X-Varnish;

    set resp.http.Server = "AuroraObjects";

    if (obj.hits == 0) {
        set resp.http.X-Cache-Hit = "No";
    } else {
        set resp.http.X-Cache-Hit = "Yes";
        set resp.http.X-Cache-Hits = obj.hits;
    }

    return (deliver);
}

sub vcl_init {
    return (ok);
}

sub vcl_fini {
    return (ok);
}
