library(ggplot2); library(ggtext)
outdir <- "tests/reference_r"
save_png <- function(name, plot) ggsave(file.path(outdir, name), plot, width = 640/72, height = 480/72, dpi = 72, device = ragg::agg_png)
test_that <- function(desc, code) code
expect_doppelganger <- function(title, p) {
  nm <- c("Rotated labels w/ colors" = "richtext_rotated_labels_w_colors.png",
          "Rotated boxes w/ colors and alignments" = "textbox_rotated_boxes_w_colors_and_alignments.png")[[title]]
  save_png(nm, p)
}
# ---- test-geom-richtext.R ----
test_that("visual tests", {
  df <- data.frame(
    x = 0.5,
    y = 0.5,
    label = "The **quick** *brown* fox.",
    angle = c(0, 45, 90, 135),
    label.colour = c("#858E4E", "#24988F", "#8C82B8", "#B97681"),
    fill = c("#E6EBD1", "#CDEFE9", "#E8E6FC", "#FEE1E5"),
    label.size = c(0.1, 0.25, 0.5, 1)
  )
  
  p <- ggplot() +
    geom_richtext(
      data = df,
      aes(
        x, y, label = label, label.colour = label.colour, fill = fill,
        label.size = label.size, angle = angle
      ),
      label.margin = grid::unit(rep(0.25, 4), "in"),
      hjust = 0, vjust = 0.5
    ) +
    xlim(0, 1) + ylim(0, 1) +
    scale_discrete_identity(aesthetics = c("orientation", "label.colour", "fill"))
  
  expect_doppelganger("Rotated labels w/ colors", p)
})

# ---- test-geom-textbox.R ----
test_that("visual tests", {
  df <- data.frame(
    x = 0.5,
    y = 0.5,
    label = "The quick brown fox **jumps over** the *lazy* dog.",
    orientation = c("upright", "left-rotated", "inverted", "right-rotated"),
    box.colour = c("#858E4E", "#24988F", "#8C82B8", "#B97681"),
    fill = c("#E6EBD1", "#CDEFE9", "#E8E6FC", "#FEE1E5"),
    halign = c(0, 0.5, 1, 0.5),
    valign = c(1, 0.5, 0.5, 0),
    box.size = c(0.1, 0.25, 0.5, 1)
  )
  
  p <- ggplot() +
    geom_textbox(
      data = df,
      aes(
        x, y, label = label, box.colour = box.colour, fill = fill,
        halign = halign, valign = valign, box.size = box.size,
        orientation = orientation
      ),
      width = grid::unit(1.5, "in"),
      height = grid::unit(1.5, "in"),
      box.margin = grid::unit(rep(0.25, 4), "in"),
      hjust = 0, vjust = 1
    ) +
    xlim(0, 1) + ylim(0, 1) +
    scale_discrete_identity(aesthetics = c("orientation", "box.colour", "fill"))
  
  expect_doppelganger("Rotated boxes w/ colors and alignments", p)
})

# ---- geom_richtext examples ----

df <- data.frame(
  label = c(
    "Some text **in bold.**",
    "Linebreaks<br>Linebreaks<br>Linebreaks",
    "*x*<sup>2</sup> + 5*x* + *C*<sub>*i*</sub>",
    "Some <span style='color:blue'>blue text **in bold.**</span><br>And *italics text.*<br>
      And some <span style='font-size:18pt; color:black'>large</span> text."
  ),
  x = c(.2, .1, .5, .9),
  y = c(.8, .4, .1, .5),
  hjust = c(0.5, 0, 0, 1),
  vjust = c(0.5, 1, 0, 0.5),
  angle = c(0, 0, 45, -45),
  color = c("black", "blue", "black", "red"),
  fill = c("cornsilk", "white", "lightblue1", "white")
)

p1 <- ggplot(df) +
  aes(
    x, y, label = label, angle = angle, color = color, fill = fill,
    hjust = hjust, vjust = vjust
  ) +
  geom_richtext() +
  geom_point(color = "black", size = 2) +
  scale_color_identity() +
  scale_fill_identity() +
  xlim(0, 1) + ylim(0, 1)
  
# labels without frame or background are also possible
p2 <- ggplot(df) +
  aes(
    x, y, label = label, angle = angle, color = color,
    hjust = hjust, vjust = vjust
  ) +
  geom_richtext(
    fill = NA, label.color = NA, # remove background and outline
    label.padding = grid::unit(rep(0, 4), "pt") # remove padding
  ) +
  geom_point(color = "black", size = 2) +
  scale_color_identity() +
  xlim(0, 1) + ylim(0, 1)

save_png("richtext_example_1.png", p1)
save_png("richtext_example_2_no_frame.png", p2)

# ---- geom_textbox example ----
df <- data.frame(
  label = rep("Lorem ipsum dolor **sit amet,** consectetur adipiscing elit,
    sed do *eiusmod tempor incididunt* ut labore et dolore magna
    aliqua.", 2),
  x = c(0, .6),
  y = c(1, .6),
  hjust = c(0, 0),
  vjust = c(1, 0),
  orientation = c("upright", "right-rotated"),
  color = c("black", "blue"),
  fill = c("cornsilk", "white")
)

p3 <- ggplot(df) +
  aes(
    x, y, label = label, color = color, fill = fill,
    hjust = hjust, vjust = vjust,
    orientation = orientation
  ) +
  geom_textbox(width = unit(0.4, "npc")) +
  geom_point(color = "black", size = 2) +
  scale_discrete_identity(aesthetics = c("color", "fill", "orientation")) +
  xlim(0, 1) + ylim(0, 1)
save_png("textbox_example.png", p3)
