@doc("An example directory service.")
package directory {

    @doc("A directory entry.")
    @value class Entry {
        String service;
        List<String> endpoints;
    }

    @doc("Access a directory service.")
    @service interface Directory {

        @doc("Lookup a directory entry.")
        @url("http://example.org/lookup")
        @query Entry lookup1(String name);

        @doc("Lookup a directory entry.")
        @url("http://example.org/lookup")
        @cache(5000) Entry lookup2(String name);

        @doc("Lookup a directory entry.")
        @url("amqp://example.org/directory")
        @index Entry lookup3(String name);

    }
}
