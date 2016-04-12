package de.meonwax.predictr.util;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * A key -> value storage that automatically sorts their values based on the keys using its {@link Comparable} interface.
 * Multiple values for the same key are allowed, thus get() will return a {@link List}.
 */
public final class SortedContainer<K extends Comparable<? super K>, V> {

    private TreeMap<K, List<V>> treeMap = new TreeMap<>();

    /**
     * Create a {@link SortedContainer} from a list of arguments.
     * Pairs of arguments are treated as key/value pairs.
     * The number of arguments needs to be even and 'null' values are allowed.
     */
    public SortedContainer(final Object... args) {
        if (args == null || args.length == 0 || args.length % 2 != 0) {
            return;
        }
        for (int i = 0; i + 1 < args.length; i += 2) {
            if (args[i] != null) {
                put((K) args[i], (V) args[i + 1]);
            }
        }
    }

    public void put(K key, V value) {
        List<V> list = treeMap.get(key);
        if (list != null) {
            list.add(value);
        }
        else {
            list = new ArrayList<>();
            list.add(value);
            treeMap.put(key, list);
        }
    }

    public List<V> get(K key) {
        return treeMap.get(key);
    }

    public List<Entry> entryList() {
        List<Entry> list = new ArrayList<>();
        for (Map.Entry<K, List<V>> entry : treeMap.entrySet()) {
            for (V t : entry.getValue()) {
                list.add(new Entry(entry.getKey(), t));
            }
        }
        return list;
    }

    public int size() {
        int size = 0;
        for (Map.Entry<K, List<V>> entry : treeMap.entrySet()) {
            size += entry.getValue().size();
        }
        return size;
    }

    public class Entry {

        private final K key;
        private V value;

        public Entry(K key, V value) {
            this.key = key;
            this.value = value;
        }

        public K getKey() {
            return key;
        }

        public V getValue() {
            return value;
        }
    }
}
