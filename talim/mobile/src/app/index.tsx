import { StyleSheet, Text, View, TouchableOpacity } from "react-native";

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Ta'lim Platformasi</Text>

      <Text style={styles.subtitle}>
        Ingliz tili, matematika va boshqa fanlarni o‘rganing
      </Text>

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>📚 Kurslar</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>🧠 Quiz</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>💬 AI Chat</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>📊 Statistikalar</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    justifyContent: "center",
    backgroundColor: "#f5f7fb",
  },

  title: {
    fontSize: 30,
    fontWeight: "700",
    textAlign: "center",
    marginBottom: 12,
  },

  subtitle: {
    fontSize: 16,
    textAlign: "center",
    color: "#666",
    marginBottom: 32,
  },

  button: {
    backgroundColor: "#2563eb",
    paddingVertical: 17,
    borderRadius: 14,
    marginBottom: 14,
  },

  buttonText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
  },
});